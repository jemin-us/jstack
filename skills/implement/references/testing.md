# 测试写法

写测试前和红绿循环中读本文件，用来判断一条测试是否值得保留。

## 好的测试

- 通过公开接口验证调用方关心的行为，内部结构整体重写后测试仍然成立。
- 测试名描述"做到了什么"，不描述"怎么做的"。例如"有效购物车可以结账"。
- 期望值来自独立的事实来源：已知正确的字面量、手算的例子、spec。
- 一条测试只验证一个行为。

```typescript
// 好：通过接口验证行为
test("创建的用户可以被查到", async () => {
  const user = await createUser({ name: "Alice" });
  expect((await getUser(user.id)).name).toBe("Alice");
});

// 差：绕过接口，直接查数据库
test("createUser 写入数据库", async () => {
  await createUser({ name: "Alice" });
  expect(await db.query("SELECT * FROM users WHERE name = ?", ["Alice"])).toBeDefined();
});
```

## 反模式

| 反模式 | 识别方法 | 改法 |
|---|---|---|
| 耦合实现 | 模拟内部模块、测私有方法、断言调用次数或顺序、绕过接口验证。行为没变，重构后测试却挂了 | 改为在接缝上断言可观察的结果 |
| 同义反复 | 期望值用和被测代码相同的方式算出来，例如 `expect(add(a, b)).toBe(a + b)`，测试永远不会失败 | 期望值改用独立的字面量 |
| 水平切片 | 先把所有测试写完，再写全部实现 | 一条测试、一段实现，循环推进 |

```typescript
// 同义反复
test("合计金额", () => {
  const items = [{ price: 10 }, { price: 5 }];
  expect(calculateTotal(items)).toBe(items.reduce((s, i) => s + i.price, 0));
});

// 改为独立字面量
test("合计金额", () => {
  expect(calculateTotal([{ price: 10 }, { price: 5 }])).toBe(15);
});
```

## 什么时候模拟

只在系统边界模拟：

- 外部 API，例如支付、邮件；
- 数据库，优先用测试库；
- 时间和随机数；
- 部分文件系统操作。

不模拟自己的模块和内部协作者。

边界处的依赖从外部传入，便于替换：

```typescript
// 便于模拟
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// 难以模拟
function processPayment(order) {
  return new StripeClient(process.env.STRIPE_KEY).charge(order.total);
}
```

外部服务按操作分别封装成函数，例如 `getUser`、`createOrder`，不要做成一个通用的 `fetch(endpoint)`。这样每个模拟只返回一种结构，也能看出测试用到了哪些接口。
