const test = require("node:test");
const assert = require("node:assert/strict");

const offerSync = require("../shared/offer-sync.js");

test("only accepts the exact Offer site origin", () => {
  assert.equal(offerSync.isOfferSiteUrl("https://offerqingbaoju.cn/home"), true);
  assert.equal(offerSync.isOfferSiteUrl("https://offerqingbaoju.cn.evil.example/"), false);
  assert.equal(offerSync.isOfferSiteUrl("not-a-url"), false);
});

test("export records retain job fields and add provenance without credentials", () => {
  const records = offerSync.createExportRecords(
    [{ 企业名称: "示例机器人", 截止时间: "2026-08-20" }],
    {
      observedAt: "2026-08-04T12:00:00.000Z",
      navigationId: 61,
      navigationName: "27届秋招",
    }
  );

  assert.equal(records[0].企业名称, "示例机器人");
  assert.equal(records[0].截止时间, "2026-08-20");
  assert.equal(records[0]._source_type, "browser_visible");
  assert.equal(records[0]._navigation_id, 61);
  assert.equal(Object.hasOwn(records[0], "token"), false);
  assert.equal(Object.hasOwn(records[0], "refreshToken"), false);
});

test("builds a deterministic dated JSONL import filename", () => {
  assert.equal(
    offerSync.buildImportFileName({
      observedAt: "2026-08-04T12:00:00.000Z",
      navigationId: 61,
    }),
    "2026-08-04_offer-nav61_raw.jsonl"
  );
});

test("serializes one JSON object per line", () => {
  const text = offerSync.toJsonl([{ a: 1 }, { b: "中文" }]);
  assert.equal(text, '{"a":1}\n{"b":"中文"}\n');
});
