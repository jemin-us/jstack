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

    def test_codex_independent_completion_requires_spawn_identity_and_return(self):
        def call(tool, receivers, states=None):
            return {'item':{'type':'collab_tool_call','status':'completed','tool':tool,'receiver_thread_ids':receivers,'agents_states':states or {}}}
        empty=call('wait',[])
        done=call('wait',['child'],{'child':{'status':'completed','message':'review result'}})
        self.assertEqual(runner.independent_reviewers([empty,done],'codex'),[])
        spawned=call('spawn_agent',['child'])
        self.assertEqual(runner.independent_reviewers([spawned,empty],'codex'),[])
        self.assertEqual(runner.independent_reviewers([spawned,done],'codex'),['child'])

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
