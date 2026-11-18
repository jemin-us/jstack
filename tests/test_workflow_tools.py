"""验证交付状态和评测器的真实边界，不运行付费模型。"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/evaluate/scripts'))
import run as runner
from cases import CASES
spec=importlib.util.spec_from_file_location('pr_state',ROOT/'skills/pr/scripts/pr_state.py')
pr_state=importlib.util.module_from_spec(spec)
spec.loader.exec_module(pr_state)


class DeliveryStateTests(unittest.TestCase):
    def setUp(self):
        self.pr={'number':1,'state':'OPEN','headRefOid':'abc','isDraft':False,'mergeable':'MERGEABLE',
                 'mergeStateStatus':'CLEAN','reviewDecision':'APPROVED','url':'https://example.invalid/pr/1',
                 'statusCheckRollup':[{'__typename':'CheckRun','status':'COMPLETED','conclusion':'SUCCESS'}]}

    def test_current_head_only(self):
        self.assertEqual(pr_state.classify(self.pr,[],'abc')['state'],'READY')
        self.assertEqual(pr_state.classify(self.pr,[],'old')['state'],'VERIFICATION_REQUIRED')

    def test_check_failure_pending_skipped_and_missing(self):
        for conclusion,expected in [('FAILURE','FAILED'),('CANCELLED','FAILED'),('SKIPPED','BLOCKED'),('NEUTRAL','BLOCKED'),(None,'BLOCKED')]:
            self.pr['statusCheckRollup'][0]['conclusion']=conclusion
            self.assertEqual(pr_state.classify(self.pr,[],'abc')['state'],expected)
        self.pr['statusCheckRollup'][0]['status']='IN_PROGRESS'
        self.assertEqual(pr_state.classify(self.pr,[],'abc')['state'],'WAITING')
        self.pr['statusCheckRollup']=[]
        self.assertEqual(pr_state.classify(self.pr,[],'abc')['state'],'BLOCKED')

    def test_unresolved_even_when_outdated(self):
        self.assertEqual(pr_state.classify(self.pr,[{'isResolved':False,'isOutdated':True}],'abc')['state'],'REVIEW_REQUIRED')
        self.assertEqual(pr_state.classify(self.pr,None,'abc')['state'],'BLOCKED')

    def test_conflicts_approvals_and_merge_queue(self):
        self.pr['mergeable']='CONFLICTING'
        self.assertEqual(pr_state.classify(self.pr,[],'abc')['state'],'BLOCKED')
        self.pr['mergeable']='MERGEABLE'
        self.pr['reviewDecision']='REVIEW_REQUIRED'
        self.assertEqual(pr_state.classify(self.pr,[],'abc')['state'],'WAITING')
        self.pr['reviewDecision']='APPROVED'
        self.pr['mergeStateStatus']='BLOCKED'
        self.assertEqual(pr_state.classify(self.pr,[],'abc')['state'],'BLOCKED')
        self.pr['state']='MERGED'
        self.assertEqual(pr_state.classify(self.pr,[],'abc')['state'],'MERGED')

    def test_paginated_threads_and_head_drift(self):
        def page(head,cursor,more):
            return {'data':{'repository':{'pullRequest':{'headRefOid':head,'reviewThreads':{'nodes':[{'isResolved':True}], 'pageInfo':{'hasNextPage':more,'endCursor':cursor}}}}}}
        with patch.object(pr_state,'gh',side_effect=[self.pr,{'owner':{'login':'o'},'name':'r'},page('abc','next',True),page('abc',None,False)]) as gh:
            _,threads=pr_state.fetch(1)
            self.assertEqual(len(threads),2)
            self.assertIn('cursor=next',gh.call_args.args)
        with patch.object(pr_state,'gh',side_effect=[self.pr,{'owner':{'login':'o'},'name':'r'},page('new',None,False)]):
            with self.assertRaises(ValueError): pr_state.fetch(1)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)

    def test_process_timeout_and_failure_preserve_logs(self):
        out,err=self.root/'out',self.root/'err'
        result=runner.execute([sys.executable,'-c','import time; print("started",flush=True); time.sleep(30)'],self.root,out,err,0.1)
        self.assertTrue(result['timed_out'])
        self.assertIn('started',out.read_text())
        result=runner.execute([sys.executable,'-c','raise SystemExit(7)'],self.root,out,err,5)
        self.assertEqual(result['exit_code'],7)

    def test_missing_client_is_blocked_with_record(self):
        with patch.object(runner.shutil,'which',return_value=None):
            result=runner.run_case('read-only','claude',None,self.root/'result',1)
        self.addCleanup(shutil_cleanup,result['workspace'])
        self.assertEqual(result['status'],'BLOCKED')
        self.assertTrue((self.root/'result/result.json').is_file())

    def test_read_only_and_protected_file_mutations(self):
        work=runner.prepare(CASES['read-only'],None,self.root)
        before={'head':runner.git(work,'rev-parse','HEAD').strip(),'branch':runner.git(work,'branch','--show-current').strip(),'protected':{}}
        self.assertEqual(runner.objective(CASES['read-only'],work,before),[])
        (work/'new.py').write_text('pass\n')
        self.assertTrue(runner.objective(CASES['read-only'],work,before))
        case={'protected':['status.py']}
        before['protected']['status.py']=runner.digest(work/'status.py')
        (work/'status.py').unlink()
        self.assertTrue(runner.objective(case,work,before))

    def test_acceptance_case_leaves_change_uncommitted_and_protected(self):
        case=CASES['accept-risky']
        work=runner.prepare(case,None,self.root)
        self.assertEqual(runner.git(work,'status','--porcelain').strip(),'M ledger.py')
        self.assertEqual((work/'ledger.py').read_text(),case['changes']['ledger.py'])
        before={'head':runner.git(work,'rev-parse','HEAD').strip(),'branch':runner.git(work,'branch','--show-current').strip(),
                'protected':{'ledger.py':runner.digest(work/'ledger.py')}}
        self.assertEqual(runner.objective(case,work,before),[])
        (work/'ledger.py').write_text(case['files']['ledger.py'])
        self.assertTrue(runner.objective(case,work,before))

    def test_success_claim_cannot_pass_broken_artifact(self):
        # 假客户端仅覆盖判据失败处理，结果绝不算模型实测。
        fake=self.root/'codex'
        fake.write_text('#!/usr/bin/env python3\nimport pathlib,sys\nif "--version" in sys.argv: print("fixture"); raise SystemExit\npathlib.Path(sys.argv[sys.argv.index("-o")+1]).write_text("全部通过")\nprint(\'{"type":"turn.completed"}\')\n')
        fake.chmod(0o755)
        with patch.dict('os.environ',{'PATH':str(self.root)+':'+__import__('os').environ['PATH']}):
            result=runner.run_case('ci-failure','codex',None,self.root/'result',10)
        self.addCleanup(shutil_cleanup,result['workspace'])
        self.assertEqual(result['status'],'FAIL')
        self.assertNotEqual(result['checks'][0]['exit_code'],0)

    def test_missing_evidence_is_blocked(self):
        fake=self.root/'codex'
        fake.write_text('#!/bin/sh\nexit 0\n');fake.chmod(0o755)
        with patch.dict('os.environ',{'PATH':str(self.root)+':'+__import__('os').environ['PATH']}):
            result=runner.run_case('read-only','codex',None,self.root/'result',10)
        self.addCleanup(shutil_cleanup,result['workspace'])
        self.assertEqual(result['status'],'BLOCKED')

    def test_source_loading_hides_criteria_and_records_fingerprint(self):
        work=runner.prepare(CASES['read-only'],ROOT,self.root)
        self.assertTrue((work/'.agents/skills/mode/SKILL.md').is_file())
        self.assertFalse((work/'.agents/skills/evaluate').exists())
        before=runner.source_digest(work)
        (work/'.agents/skills/mode/SKILL.md').write_text('changed')
        self.assertNotEqual(runner.source_digest(work),before)

    def test_invalid_events_and_missing_terminal_are_not_success(self):
        path=self.root/'events'
        for text in ['not-json', '{}', '{"type":"turn.failed"}']:
            path.write_text(text)
            with self.assertRaises(ValueError): runner.event_summary(path,'codex')

    def test_claude_string_message_and_content_are_counted_without_crash(self):
        path=self.root/'events'
        path.write_text('\n'.join([
            '{"type":"user","message":{"role":"user","content":"纯文本"}}',
            '{"type":"system","subtype":"notice","message":"字符串形式的 message"}',
            '{"type":"assistant","message":{"content":[{"type":"tool_use","id":"t1","name":"Read","input":{}}]}}',
            '{"type":"result","subtype":"success","is_error":false}']))
        self.assertEqual(runner.event_summary(path,'claude')['tool_events'],1)

    def test_codex_independent_completion_requires_spawn_identity_and_return(self):
        def call(tool, receivers, states=None):
            return {'item':{'type':'collab_tool_call','status':'completed','tool':tool,'receiver_thread_ids':receivers,'agents_states':states or {}}}
        empty=call('wait',[])
        done=call('wait',['child'],{'child':{'status':'completed','message':'review result'}})
        self.assertEqual(runner.independent_reviewers([empty,done],'codex'),[])
        spawned=call('spawn_agent',['child'])
        self.assertEqual(runner.independent_reviewers([spawned,empty],'codex'),[])
        self.assertEqual(runner.independent_reviewers([spawned,done],'codex'),['child'])

    @staticmethod
    def codex_child(agent_path, own_tools, inherited_tools=()):
        # 结构取自 codex-cli 0.169 的真实子线程 rollout：开头继承父线程历史，ordinal 之后才是子 agent 自己的记录。
        def item(payload): return {'type':'response_item','payload':payload}
        inherited=[item({'type':'custom_tool_call','name':name,'call_id':f'p{i}'}) for i,name in enumerate(inherited_tools)]
        inherited+=[item({'type':'custom_tool_call_output','call_id':f'p{i}'}) for i,_ in enumerate(inherited_tools)]
        start=1+len(inherited)
        meta={'type':'session_meta','payload':{'parent_thread_id':'t1','agent_path':agent_path,'subagent_history_start_ordinal':start}}
        own=[]
        for i,name in enumerate(own_tools):
            own+=[item({'type':'custom_tool_call','name':name,'call_id':f'o{i}'}),item({'type':'custom_tool_call_output','call_id':f'o{i}'})]
        return [meta,*inherited,*own]

    def test_codex_rollout_completion_requires_spawn_answer_and_child_tool_run(self):
        # 结构取自 codex-cli 0.169 的真实 rollout，已删去提示词与密文。
        def item(payload): return {'type':'response_item','payload':payload}
        spawn=item({'type':'function_call','name':'spawn_agent','call_id':'c1','arguments':'{}'})
        output=item({'type':'function_call_output','call_id':'c1','output':'{"task_name":"/root/review"}'})
        def answer(author, payload): return item({'type':'agent_message','author':author,'recipient':'/root',
            'content':[{'type':'input_text','text':f'Message Type: FINAL_ANSWER\nTask name: /root\nSender: {author}\nPayload:\n{payload}'}]})
        ran={'/root/review':self.codex_child('/root/review',['exec'])}
        self.assertEqual(runner.rollout_reviewers([spawn,output,answer('/root/review','FAIL')],ran),{'/root/review'})
        self.assertEqual(runner.rollout_reviewers([spawn,answer('/root/review','FAIL')],ran),set())
        self.assertEqual(runner.rollout_reviewers([spawn,output,answer('/root/other','FAIL')],ran),set())
        self.assertEqual(runner.rollout_reviewers([spawn,output,answer('/root/review','')],ran),set())
        failed=item({'type':'function_call_output','call_id':'c1','output':'collab spawn failed: no rollout found'})
        self.assertEqual(runner.rollout_reviewers([spawn,failed,answer('/root/review','FAIL')],ran),set())
        # 子线程缺失、只有协作工具、只有继承来的父线程调用，都不能证明子 agent 实际执行过。
        self.assertEqual(runner.rollout_reviewers([spawn,output,answer('/root/review','FAIL')],{}),set())
        idle={'/root/review':self.codex_child('/root/review',['wait_agent'],inherited_tools=['exec'])}
        self.assertEqual(runner.rollout_reviewers([spawn,output,answer('/root/review','FAIL')],idle),set())

    def test_codex_rollouts_are_found_by_thread_and_merged_into_summary(self):
        home=self.root/'codex-home'; day=home/'sessions/2026/11/15'; day.mkdir(parents=True)
        def write(path, records): path.write_text('\n'.join(json.dumps(x) for x in records)+'\n'); return path
        rollout=write(day/'rollout-2026-11-15T00-00-00-t1.jsonl',[
            {'type':'session_meta','payload':{'id':'t1'}},
            {'type':'response_item','payload':{'type':'function_call','name':'spawn_agent','call_id':'c1'}},
            {'type':'response_item','payload':{'type':'function_call_output','call_id':'c1','output':'{"task_name":"/root/r"}'}},
            {'type':'response_item','payload':{'type':'agent_message','author':'/root/r','content':[{'type':'input_text','text':'FINAL_ANSWER\nPayload:\nok'}]}}])
        child=write(day/'rollout-2026-11-15T00-00-01-t2.jsonl',self.codex_child('/root/r',['exec']))
        write(day/'rollout-2026-11-15T00-00-02-t3.jsonl',[{'type':'session_meta','payload':{'parent_thread_id':'other','agent_path':'/root/x'}}])
        events=self.root/'events.jsonl'
        events.write_text('{"type":"thread.started","thread_id":"t1"}\n{"type":"turn.completed","usage":{}}\n')
        with patch.dict('os.environ',{'CODEX_HOME':str(home)}):
            found,children=runner.find_rollouts([{'type':'thread.started','thread_id':'t1'}])
            self.assertEqual((found,children),(rollout,{'/root/r':child}))
            self.assertEqual(runner.find_rollouts([{'type':'thread.started','thread_id':'missing'}]),(None,{}))
        self.assertEqual(runner.event_summary(events,'codex',rollout,children)['independent_reviewers'],['/root/r'])
        self.assertEqual(runner.event_summary(events,'codex',rollout)['independent_reviewers'],[])
        self.assertEqual(runner.event_summary(events,'codex')['independent_reviewers'],[])

    def test_codex_child_rollout_found_after_midnight(self):
        home=self.root/'codex-home'
        day=home/'sessions/2026/12/31'; day.mkdir(parents=True)
        nextday=home/'sessions/2027/01/01'; nextday.mkdir(parents=True)
        parent=day/'rollout-2026-12-31T23-59-59-t1.jsonl'; parent.write_text('{"type":"session_meta","payload":{"id":"t1"}}\n')
        child=nextday/'rollout-2027-01-01T00-00-01-t2.jsonl'
        child.write_text(json.dumps({'type':'session_meta','payload':{'parent_thread_id':'t1','agent_path':'/root/r'}})+'\n')
        with patch.dict('os.environ',{'CODEX_HOME':str(home)}):
            self.assertEqual(runner.find_rollouts([{'type':'thread.started','thread_id':'t1'}]),(parent,{'/root/r':child}))

    def test_codex_rollout_outside_dated_folders_does_not_crash(self):
        home=self.root/'codex-home'; folder=home/'sessions/archive/x/y'; folder.mkdir(parents=True)
        parent=folder/'rollout-a-t1.jsonl'; parent.write_text('{"type":"session_meta","payload":{"id":"t1"}}\n')
        child=folder/'rollout-b-t2.jsonl'
        child.write_text(json.dumps({'type':'session_meta','payload':{'parent_thread_id':'t1','agent_path':'/root/r'}})+'\n')
        with patch.dict('os.environ',{'CODEX_HOME':str(home)}):
            self.assertEqual(runner.find_rollouts([{'type':'thread.started','thread_id':'t1'}]),(parent,{'/root/r':child}))

    def test_codex_rollout_on_last_representable_day_does_not_crash(self):
        home=self.root/'codex-home'; day=home/'sessions/9999/12/31'; day.mkdir(parents=True)
        parent=day/'rollout-a-t1.jsonl'; parent.write_text('{"type":"session_meta","payload":{"id":"t1"}}\n')
        child=day/'rollout-b-t2.jsonl'
        child.write_text(json.dumps({'type':'session_meta','payload':{'parent_thread_id':'t1','agent_path':'/root/r'}})+'\n')
        with patch.dict('os.environ',{'CODEX_HOME':str(home)}):
            self.assertEqual(runner.find_rollouts([{'type':'thread.started','thread_id':'t1'}]),(parent,{'/root/r':child}))

    def test_forget_trust_accepts_other_valid_toml_header_spellings(self):
        home=self.root/'codex-home'; home.mkdir()
        work=self.root/'workspace-a'/'project'; work.mkdir(parents=True)
        path=str(work.resolve()); config=home/'config.toml'
        tail='[projects."/x/workspace-b/project"]\ntrust_level = "trusted"\n'
        for header in (f"[projects.'{path}']", f'[ projects . "{path}" ]  # 临时', f'  [projects."{path}"]'):
            config.write_text(f'model = "m"\n{header}\ntrust_level = "trusted"\n[projects."{path}".extra]\nx = 1\n{tail}')
            with patch.dict('os.environ',{'CODEX_HOME':str(home)}):
                self.assertTrue(runner.forget_trust(work), header)
                self.assertEqual(config.read_text(),f'model = "m"\n{tail}', header)

    def test_forget_trust_ignores_brackets_inside_multiline_values(self):
        home=self.root/'codex-home'; home.mkdir()
        work=self.root/'workspace-a'/'project'; work.mkdir(parents=True)
        path=str(work.resolve()); config=home/'config.toml'
        other=f'[notes]\ntext = """\n[projects."{path}"]\n"""\n'
        tail='[projects."/x/workspace-b/project"]\ntrust_level = "trusted"\n'
        config.write_text(f'{other}[projects."{path}"]\narr = [\n  ["x"],\n]\ns = \'\'\'\n[other]\n\'\'\'\n{tail}')
        with patch.dict('os.environ',{'CODEX_HOME':str(home)}):
            self.assertTrue(runner.forget_trust(work))
            self.assertEqual(config.read_text(),other+tail)

    def test_forget_trust_leaves_unparseable_config_untouched(self):
        home=self.root/'codex-home'; home.mkdir()
        work=self.root/'workspace-a'/'project'; work.mkdir(parents=True)
        config=home/'config.toml'
        text=f'[projects."{work.resolve()}"]\nk = 1\nk = 2\n[projects."/x/b"]\ntrust_level = "trusted"\n[mcp]\nx = 1\n'
        config.write_text(text)
        with patch.dict('os.environ',{'CODEX_HOME':str(home)}):
            self.assertFalse(runner.forget_trust(work))
            self.assertEqual(config.read_text(),text)

    def forget_in(self, text, binary=False):
        home=self.root/'codex-home'; home.mkdir(exist_ok=True)
        work=self.root/'workspace-a'/'project'; work.mkdir(parents=True, exist_ok=True)
        text=text.replace('WS',str(work.resolve())); config=home/'config.toml'
        config.write_bytes(text.encode())
        with patch.dict('os.environ',{'CODEX_HOME':str(home)}):
            return runner.forget_trust(work), config.read_bytes().decode()

    def test_forget_trust_removes_dotted_and_inline_forms(self):
        other='[projects."/x/b"]\ntrust_level = "trusted"\n'
        forms=['[projects]\n"WS".trust_level = "trusted"\n',
               '[projects]\n"WS" = { trust_level = "trusted" }\n',
               'projects."WS".trust_level = "trusted"\n']
        ok,text=self.forget_in('model = "m"\nprojects = { "WS" = { trust_level = "trusted" } }\n[features]\nx = 1\n')
        self.assertTrue(ok)
        self.assertEqual(text,'model = "m"\n[features]\nx = 1\n')
        for form in forms:
            ok,text=self.forget_in('model = "m"\n'+form+other)
            self.assertTrue(ok, form)
            self.assertNotIn(str((self.root/'workspace-a'/'project').resolve()), text, form)
            self.assertIn(other, text, form)
            self.assertEqual(runner.tomllib.loads(text)['projects'], {'/x/b':{'trust_level':'trusted'}}, form)

    def test_forget_trust_leaves_shared_inline_table_untouched(self):
        text='projects = { "WS" = { trust_level = "trusted" }, "/x/b" = { trust_level = "trusted" } }\n'
        ok,after=self.forget_in(text)
        self.assertFalse(ok)
        self.assertEqual(after, text.replace('WS',str((self.root/'workspace-a'/'project').resolve())))

    def test_forget_trust_keeps_crlf_line_endings(self):
        ok,text=self.forget_in('model = "m"\r\n[projects."WS"]\r\ntrust_level = "trusted"\r\n[features]\r\nx = 1\r\n')
        self.assertTrue(ok)
        self.assertEqual(text,'model = "m"\r\n[features]\r\nx = 1\r\n')

    def test_forget_trust_keeps_comments_that_are_not_inside_the_entry(self):
        ok,text=self.forget_in('# a\u2028b\n\n# about WS\n[projects."WS"]\nt = 1\n# inside\nu = 2\n\n# before b\n[projects."/x/b"]\nt = 1\n# tail\n')
        self.assertTrue(ok)
        ws=str((self.root/'workspace-a'/'project').resolve())
        self.assertEqual(text,f'# a\u2028b\n\n# about {ws}\n# before b\n[projects."/x/b"]\nt = 1\n# tail\n')

    def test_forget_trust_skips_config_that_is_not_utf8(self):
        home=self.root/'codex-home'; home.mkdir()
        config=home/'config.toml'; data='# caf\u00e9\n[projects."/w/a"]\nt = 1\n'.encode('latin-1')
        config.write_bytes(data)
        with patch.dict('os.environ',{'CODEX_HOME':str(home)}):
            self.assertFalse(runner.forget_trust('/w/a'))
        self.assertEqual(config.read_bytes(),data)

    def test_forget_trust_only_drops_comments_between_removed_lines(self):
        cases={'x = 1\n# about x2\nprojects."WS".t = 1\nx2 = 1\n':'x = 1\n# about x2\nx2 = 1\n',
               '[projects]\n"/x/b".t = 1\n# note about b\n\n"WS".t = 1\n':'[projects]\n"/x/b".t = 1\n# note about b\n\n',
               '[projects."WS"]\nt = 1\n\n# about y\n\n[y]\nz = 1\n':'# about y\n\n[y]\nz = 1\n'}
        for before,after in cases.items():
            ok,text=self.forget_in(before)
            self.assertTrue(ok, before)
            self.assertEqual(text, after, before)

    def test_forget_trust_reports_unreadable_config(self):
        for data in ('[projects."/w/a"]\nt = \n'.encode(), '# caf\u00e9\n'.encode('latin-1')):
            home=self.root/'codex-home'; home.mkdir(exist_ok=True); (home/'config.toml').write_bytes(data)
            with patch.dict('os.environ',{'CODEX_HOME':str(home)}), patch('sys.stderr') as err:
                self.assertFalse(runner.forget_trust('/w/a'))
            self.assertIn('未清理', ''.join(call.args[0] for call in err.write.call_args_list), data)

    def test_forget_trust_drops_comments_between_removed_tables(self):
        cases={'[projects."WS"]\nt = 1\n# sub\n[projects."WS".sub]\nx = 1\n\n[z]\nq = 1\n':'[z]\nq = 1\n',
               '[[projects."WS".hooks]]\na = 1\n# between hooks\n[[projects."WS".hooks]]\na = 2\n[projects."/x/b"]\nt = 1\n':'[projects."/x/b"]\nt = 1\n'}
        for before,after in cases.items():
            ok,text=self.forget_in(before)
            self.assertTrue(ok, before)
            self.assertEqual(text, after, before)

    def test_forget_trust_removes_only_this_workspace_section(self):
        home=self.root/'codex-home'; home.mkdir()
        work=self.root/'workspace-a'/'project'; work.mkdir(parents=True)
        other='[projects."/x/workspace-b/project"]\ntrust_level = "trusted"\n'
        config=home/'config.toml'
        config.write_text(f'model = "m"\n\n[projects."{work.resolve()}"]\ntrust_level = "trusted"\n\n{other}[features]\nmulti_agent_v2 = true\n')
        with patch.dict('os.environ',{'CODEX_HOME':str(home)}):
            self.assertTrue(runner.forget_trust(work))
            self.assertEqual(config.read_text(),f'model = "m"\n\n{other}[features]\nmulti_agent_v2 = true\n')
            self.assertFalse(runner.forget_trust(work))
            self.assertFalse(runner.forget_trust(self.root/'missing'))

    def test_client_commands_keep_rollout_and_sandbox_bash(self):
        codex=runner.command('codex',self.root,self.root/'r.txt')
        self.assertNotIn('--ephemeral',codex)
        claude=runner.command('claude',self.root,self.root/'r.txt')
        settings=json.loads(claude[claude.index('--settings')+1])
        self.assertTrue(settings['sandbox']['enabled'] and settings['sandbox']['autoAllowBashIfSandboxed'])
        self.assertNotIn('bypassPermissions',claude)
        agy=runner.command('agy',self.root,self.root/'r.txt','- leading dash prompt')
        agy_settings=json.loads(agy[agy.index('--settings')+1])
        self.assertTrue(agy_settings['enableTerminalSandbox'])
        self.assertEqual(agy_settings['toolPermission'],'proceed-in-sandbox')
        self.assertIn('--print=- leading dash prompt',agy)
        self.assertNotIn('--dangerously-skip-permissions',agy)

    def test_claude_independent_completion_rejects_errors_background_and_unmatched(self):
        call={'message':{'content':[{'type':'tool_use','name':'Agent','id':'a','input':{}}]}}
        done={'message':{'content':[{'type':'tool_result','tool_use_id':'a','content':'result'}]}}
        self.assertEqual(runner.independent_reviewers([done],'claude'),[])
        self.assertEqual(runner.independent_reviewers([call,done],'claude'),['a'])
        done['message']['content'][0]['is_error']=True
        self.assertEqual(runner.independent_reviewers([call,done],'claude'),[])
        done['message']['content'][0]['is_error']=False
        call['message']['content'][0]['input']['run_in_background']=True
        self.assertEqual(runner.independent_reviewers([call,done],'claude'),[])

    def test_claude_missing_identity_cannot_prove_completion(self):
        events=[{'message':{'content':[{'type':'tool_use','name':'Agent','input':{}}]}},
                {'message':{'content':[{'type':'tool_result','content':'claimed result'}]}}]
        self.assertEqual(runner.independent_reviewers(events,'claude'),[])

    @staticmethod
    def agy_child(own_tools, status='DONE'):
        # 结构取自 agy 1.5.10 的真实子代理 transcript_full.jsonl，已删去提示词与机器路径。
        steps=[{'step_index':0,'source':'SYSTEM','type':'SYSTEM_MESSAGE','status':'DONE','content':'brief'}]
        idx=1
        for name in own_tools:
            steps.append({'step_index':idx,'source':'MODEL','type':'PLANNER_RESPONSE','status':'DONE',
                          'tool_calls':[{'name':name,'args':{}}]})
            steps.append({'step_index':idx+1,'source':'MODEL','type':'GENERIC','status':status,'content':'tool output' if status=='DONE' else ''})
            idx+=2
        steps.append({'step_index':idx,'source':'MODEL','type':'PLANNER_RESPONSE','status':'DONE','content':'done'})
        return steps

    def test_agy_transcript_completion_requires_spawn_reply_and_child_tool_run(self):
        spawn={'step_index':1,'source':'MODEL','type':'PLANNER_RESPONSE','status':'DONE',
               'tool_calls':[{'name':'invoke_subagent','args':{'TypeName':'"self"'}}]}
        created={'step_index':2,'source':'MODEL','type':'GENERIC','status':'DONE',
                 'content':'Created At: t\nCompleted At: t\nCreated the following subagent:\n{\n  "conversationId": "c1"\n}\n'}
        def reply(sender, body):
            return {'step_index':5,'source':'SYSTEM','type':'SYSTEM_MESSAGE','status':'DONE',
                    'content':f'<SYSTEM_MESSAGE>\n[Message] timestamp=2026-11-18T00:00:00Z sender={sender} priority=MESSAGE_PRIORITY_HIGH content={body}\n</SYSTEM_MESSAGE>'}
        ran={'c1':self.agy_child(['run_command','send_message'])}
        self.assertEqual(runner.transcript_reviewers([spawn,created,reply('c1','FAIL')],ran),{'c1'})
        self.assertEqual(runner.transcript_reviewers([created,reply('c1','FAIL')],ran),set())
        self.assertEqual(runner.transcript_reviewers([spawn,reply('c1','FAIL')],ran),set())
        self.assertEqual(runner.transcript_reviewers([spawn,created,reply('other','FAIL')],ran),set())
        self.assertEqual(runner.transcript_reviewers([spawn,created,reply('c1','   ')],ran),set())
        self.assertEqual(runner.transcript_reviewers([spawn,created,reply('c1','FAIL')],{}),set())
        self.assertEqual(runner.transcript_reviewers([spawn,created,reply('c1','FAIL')],{'c1':self.agy_child(['send_message'])}),set())
        self.assertEqual(runner.transcript_reviewers([spawn,created,reply('c1','FAIL')],{'c1':self.agy_child(['run_command'],status='ERROR')}),set())

    def test_agy_transcripts_are_found_and_merged_into_summary(self):
        home=self.root/'agy-home'
        def write_log(cid, steps):
            p=home/'brain'/cid/'.system_generated/logs/transcript_full.jsonl'
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text('\n'.join(json.dumps(x) for x in steps)+'\n')
            return p
        parent=write_log('p1',[
            {'step_index':0,'source':'USER_EXPLICIT','type':'USER_INPUT','status':'DONE','content':'task'},
            {'step_index':1,'source':'MODEL','type':'PLANNER_RESPONSE','status':'DONE','tool_calls':[{'name':'run_command'},{'name':'invoke_subagent'}]},
            {'step_index':2,'source':'MODEL','type':'GENERIC','status':'DONE','content':'ok'},
            {'step_index':3,'source':'MODEL','type':'GENERIC','status':'DONE','content':'Created the following subagent:\n{"conversationId":"c1"}\n'},
            {'step_index':4,'source':'SYSTEM','type':'SYSTEM_MESSAGE','status':'DONE','content':'<SYSTEM_MESSAGE>\n[Message] timestamp=t sender=c1 priority=HIGH content=PASS\n</SYSTEM_MESSAGE>'},
            {'step_index':5,'source':'MODEL','type':'PLANNER_RESPONSE','status':'DONE','content':'final report'}])
        child=write_log('c1',self.agy_child(['read_file','run_command']))
        write_log('unrelated',self.agy_child(['run_command']))
        events_list=[
            {'event':'init','conversation_id':'p1','init':{'cwd':str(self.root)}},
            {'event':'step_update','step_update':{'conversation_id':'p1','state':'DONE','step_type':'subagent','tool_name':'invoke_subagent',
                                                  'subagent_info':{'subagents':[{'conversation_id':'c1'},{'conversation_id':'../escape'}]}}},
            {'event':'result','result':{'conversation_id':'p1','status':'SUCCESS','response':'final report','usage':{'total_tokens':10}}}]
        events=self.root/'events.jsonl'
        events.write_text('\n'.join(json.dumps(x) for x in events_list)+'\n')
        with patch.dict('os.environ',{'AGY_HOME':str(home)}):
            found,children=runner.find_transcripts(events_list)
            self.assertEqual((found,children),(parent,{'c1':child}))
        summary=runner.event_summary(events,'agy',parent,children)
        self.assertEqual(summary['tool_events'],2)
        self.assertEqual(summary['independent_reviewers'],['c1'])
        # 瞬时重试留下 ERROR 标记时，仅在非超时中断且父 transcript 已正常完成最终回复时接纳；无 transcript 时拒绝。
        events_list[-1]={'event':'result','result':{'conversation_id':'p1','status':'ERROR','finished_reason':'error','response':'final report','usage':{}}}
        events.write_text('\n'.join(json.dumps(x) for x in events_list)+'\n')
        self.assertEqual(runner.event_summary(events,'agy',parent,children)['independent_reviewers'],['c1'])
        with self.assertRaises(ValueError):
            runner.event_summary(events,'agy')
        events_list[-1]['result']['finished_reason']='print_timeout'
        events.write_text('\n'.join(json.dumps(x) for x in events_list)+'\n')
        with self.assertRaises(ValueError):
            runner.event_summary(events,'agy',parent,children)

    def test_artifacts_survive_symlinked_temporary_root(self):
        actual=self.root/'actual'; actual.mkdir()
        link=self.root/'alias'; link.symlink_to(actual,target_is_directory=True)
        work=runner.prepare(CASES['read-only'],None,link)
        (work/'screens').mkdir()
        (work/'screens/screenshot.png').write_bytes(b'png evidence')
        (work/'external').symlink_to('/etc/hosts')
        destination=self.root/'result'
        runner.preserve_files(work,destination)
        self.assertEqual((destination/'artifacts/screens/screenshot.png').read_bytes(),b'png evidence')
        self.assertEqual((destination/'artifacts/status.py').read_text(),CASES['read-only']['files']['status.py'])
        self.assertFalse((destination/'artifacts/external').exists())
        self.assertEqual((destination/'artifacts/external.symlink.txt').read_text(),'/etc/hosts')

    def test_bad_arguments_and_existing_output(self):
        script=ROOT/'skills/evaluate/scripts/run.py'
        result=subprocess.run([sys.executable,str(script),'--repeat','0'],capture_output=True)
        self.assertNotEqual(result.returncode,0)
        (self.root/'read-only-1').mkdir()
        result=subprocess.run([sys.executable,str(script),'--client','codex','--case','read-only','--out',str(self.root)],capture_output=True)
        self.assertNotEqual(result.returncode,0)


def shutil_cleanup(workspace):
    import shutil
    shutil.rmtree(Path(workspace).parent)


if __name__=='__main__': unittest.main()
