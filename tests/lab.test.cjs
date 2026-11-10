const test = require("node:test");
const assert = require("node:assert/strict");
const core = require("../docs/core.js");
const converter = require("../docs/assets/cvnss-converter.js");

test("CVNSS4.0 audit-safe v5 self-check and known ambiguity groups", () => {
  const result = converter.selfTest();
  assert.equal(result.ok, true, JSON.stringify(result.failures));
  assert.equal(result.tests, 23);
  assert.equal(converter.audit().ambiguityGroups, 56);
  assert.equal(converter.audit().criticalCollisionGroups, 5);
  assert.equal(converter.audit().silentReverseOverwrite, 0);
});

test("all 27 symbols map bijectively into three trits", () => {
  for (let i = 0; i < 27; i++) {
    const d = core.indexToTrits(i);
    assert.equal(core.tritsToIndex(d), i);
    assert.equal(core.balancedValue(d.map(x => x - 1)), i - 13);
    const sym = core.ALPHABET[i];
    assert.equal(core.tritsToSymbol(core.symbolToTrits(sym)), sym);
  }
  assert.equal(core.decodeBase27(core.encodeBase27("VIET NAM")), "VIET NAM");
  assert.throws(() => core.encodeBase27("VIỆT NAM"), /Base27/);
});

test("five-trits-per-byte packing is lossless with original length", () => {
  for (let count = 0; count <= 102; count++) {
    const trits = Array.from({length: count}, (_, i) => (i * 7 + count) % 3 - 1);
    const packed = core.pack5(trits);
    assert.equal(packed.length, Math.ceil(count / 5));
    assert.deepEqual(core.unpack5(packed, count), trits);
    assert.ok(packed.every(b => b >= 0 && b < 243));
  }
  assert.equal(core.pack5([-1, -1, -1, -1, -1])[0], 0);
  assert.equal(core.pack5([1, 1, 1, 1, 1])[0], 242);
  assert.throws(() => core.unpack5([250], 5), /outside/);
});

test("balanced addition and ternary multiply preserve trit domain", () => {
  for (const a of [-1, 0, 1]) for (const b of [-1, 0, 1]) {
    assert.ok([-1, 0, 1].includes(core.wrap(a + b)));
    assert.ok([-1, 0, 1].includes(a * b));
  }
  assert.equal(core.wrap(2), -1);
  assert.equal(core.wrap(-2), 1);
});

test("typed BilaTiny subset compiles into bytes and runs in VM", () => {
  const src = [
    "trit a = +1;",
    "trit b = +1;",
    "trit c = tadd(a, b);",
    "trit d = tmul(c, b);",
    "emit(d);"
  ].join("\n");
  const compiled = core.compileTiny(src);
  assert.equal(compiled.instructionCount, 6);
  assert.equal(compiled.bytes.length, 24);
  assert.deepEqual(core.runTiny(compiled.bytes).outputs, [-1]);
  assert.match(compiled.asm, /TADD/);
  assert.throws(() => core.compileTiny("trit a = foo; emit(a);"), /chưa hỗ trợ/);
  assert.throws(() => core.compileTiny("trit a = 1;"), /emit/);
});

test("synthetic quantization is deterministic, reports real sizes, not claimed speed", () => {
  const a = core.simulateQuant(0.3);
  const b = core.simulateQuant(0.3);
  assert.deepEqual(a.quantized, b.quantized);
  assert.deepEqual(a.fp, b.fp);
  assert.equal(a.quantized.length, 128);
  assert.equal(a.fp32Bytes, 512);
  assert.equal(a.bytePack5, 26);
  assert.equal(a.twoBitBytes, 32);
  assert.equal(a.skipped + a.nonzero, 128);
  assert.ok(Number.isFinite(a.mse));
  const zero = core.simulateQuant(1.5);
  assert.equal(zero.nonzero, 0);
  assert.deepEqual(zero.tq, Array(8).fill(0));
});
