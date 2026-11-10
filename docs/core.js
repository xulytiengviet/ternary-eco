/* Ternary Eco Lab reference core. Pure JS, Node + browser, deterministic.
   Logical trits run on ordinary binary hardware; not a native ternary ISA. */
(function(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.TernaryCore = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function() {
  "use strict";
  const ALPHABET = " ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  const validTrit = x => Number.isInteger(x) && x >= -1 && x <= 1;
  const wrap = x => ((x + 1) % 3 + 3) % 3 - 1;

  function indexToTrits(index) {
    if (!Number.isInteger(index) || index < 0 || index >= 27) throw Error("Base27 index must be 0–26");
    return [Math.floor(index / 9), Math.floor(index / 3) % 3, index % 3];
  }
  function tritsToIndex(digits) {
    if (!Array.isArray(digits) || digits.length !== 3 || digits.some(x => !Number.isInteger(x) || x < 0 || x > 2)) throw Error("Exactly three unbalanced trits 0/1/2 required");
    return digits[0] * 9 + digits[1] * 3 + digits[2];
  }
  function symbolToTrits(ch) {
    const index = ALPHABET.indexOf(ch);
    if (index < 0 || ch.length !== 1) throw Error("Unsupported Base27 character: " + ch);
    return indexToTrits(index);
  }
  function tritsToSymbol(digits) { return ALPHABET[tritsToIndex(digits)]; }
  function encodeBase27(text) {
    const value = String(text);
    const unsupported = Array.from(value).filter(c => !ALPHABET.includes(c));
    if (unsupported.length) throw Error("Base27 chỉ nhận A–Z và SPACE. Ký tự không hỗ trợ: " + Array.from(new Set(unsupported)).join(" "));
    return Array.from(value).flatMap(symbolToTrits);
  }
  function decodeBase27(trits) {
    if (!Array.isArray(trits) || trits.length % 3 !== 0) throw Error("Base27 trit count must be divisible by 3");
    let result = "";
    for (let i = 0; i < trits.length; i += 3) result += tritsToSymbol(trits.slice(i, i + 3));
    return result;
  }
  function balancedValue(digits) {
    if (!Array.isArray(digits) || digits.some(x => !validTrit(x))) throw Error("Balanced trits must be −1/0/+1");
    return digits.reduce((v, t) => v * 3 + t, 0);
  }
  function balancedText(digits) {
    if (!Array.isArray(digits) || digits.some(x => !validTrit(x))) throw Error("Invalid balanced trits");
    return digits.map(x => x === -1 ? "T" : String(x)).join("");
  }
  function parseBalancedText(text) {
    const s = String(text).trim().toUpperCase();
    if (!/^[T01]+$/.test(s)) throw Error("Dùng T = −1, 0, 1, không nhập ký tự khác");
    return Array.from(s).map(x => x === "T" ? -1 : Number(x));
  }
  // One byte stores five balanced trits: digits 0/1/2 correspond to -1/0/+1.
  // 3^5=243, leaving 13 of 256 byte values unused. Length is external metadata.
  function pack5(trits) {
    if (!Array.isArray(trits) || trits.some(x => !validTrit(x))) throw Error("Expected array of balanced trits");
    const bytes = [];
    for (let i = 0; i < trits.length; i += 5) {
      let byte = 0;
      for (let j = 0; j < 5; j++) byte = byte * 3 + ((i + j < trits.length ? trits[i + j] : 0) + 1);
      bytes.push(byte);
    }
    return bytes;
  }
  function unpack5(bytes, count) {
    if (!Array.isArray(bytes) || bytes.some(x => !Number.isInteger(x) || x < 0 || x >= 243)) throw Error("Packed byte outside 0..242");
    if (!Number.isInteger(count) || count < 0 || count > bytes.length * 5 || (bytes.length > 0 && count <= (bytes.length - 1) * 5)) throw Error("Invalid original trit count");
    const trits = [];
    for (const b of bytes) {
      let n = b;
      const group = Array(5).fill(0);
      for (let j = 4; j >= 0; j--) { group[j] = (n % 3) - 1; n = Math.floor(n / 3); }
      trits.push(...group);
    }
    return trits.slice(0, count);
  }
  function byteHex(bytes) { return bytes.map(b => b.toString(16).toUpperCase().padStart(2, "0")).join(" "); }

  // Deliberately small, typed educational BilaTiny subset, not the full BilaScript compiler.
  // One instruction = [opcode, rd, a, b] as ordinary 8-bit bytes in a teaching VM.
  const OPCODES = Object.freeze({ HALT: 0, SET: 1, TADD: 2, TMUL: 3, EMIT: 4 });
  function compileTiny(source) {
    const cleaned = String(source).replace(/\/\/[^\n]*/g, "").replace(/#[^\n]*/g, "");
    const stmts = cleaned.split(";").map(s => s.trim()).filter(Boolean);
    if (!stmts.length || stmts.length > 64) throw Error("Chương trình cần 1–64 câu lệnh kết thúc bằng dấu ;");
    const vars = new Map(), inst = [], asm = [];
    let hasEmit = false;
    const reg = name => {
      if (!vars.has(name)) throw Error("Biến chưa khai báo: " + name);
      return vars.get(name);
    };
    stmts.forEach((s, i) => {
      const declaration = s.match(/^trit\s+([a-zA-Z_]\w*)\s*=\s*(.*?)$/);
      const output = s.match(/^emit\s*\(\s*([a-zA-Z_]\w*)\s*\)$/);
      if (declaration) {
        const name = declaration[1], rhs = declaration[2].trim();
        if (vars.has(name)) throw Error("Biến trùng: " + name);
        if (vars.size >= 8) throw Error("BilaTiny VM chỉ có 8 thanh ghi");
        const rd = vars.size; vars.set(name, rd);
        if (/^[+-]?1$|^0$/.test(rhs)) {
          const n = Number(rhs); if (!validTrit(n)) throw Error("Giá trị trit không hợp lệ");
          inst.push([OPCODES.SET, rd, n + 1, 0]);
          asm.push("SET R" + rd + ", " + (n > 0 ? "+" : "") + n + "   ; " + name);
        } else {
          const expr = rhs.match(/^(tadd|tmul)\s*\(\s*([a-zA-Z_]\w*)\s*,\s*([a-zA-Z_]\w*)\s*\)$/);
          if (!expr) throw Error("Biểu thức chưa hỗ trợ tại lệnh " + (i + 1) + ": " + rhs);
          const ra = reg(expr[2]), rb = reg(expr[3]);
          const opcode = expr[1] === "tadd" ? OPCODES.TADD : OPCODES.TMUL;
          inst.push([opcode, rd, ra, rb]);
          asm.push(expr[1].toUpperCase() + " R" + rd + ", R" + ra + ", R" + rb + "   ; " + name);
        }
      } else if (output) {
        const rs = reg(output[1]);
        inst.push([OPCODES.EMIT, rs, 0, 0]); asm.push("EMIT R" + rs); hasEmit = true;
      } else throw Error("Cú pháp không hỗ trợ tại lệnh " + (i + 1) + ": " + s);
    });
    if (!hasEmit) throw Error("Hãy dùng emit(tên_biến); để xuất kết quả");
    inst.push([OPCODES.HALT, 0, 0, 0]); asm.push("HALT");
    return { bytes: inst.flat(), asm: asm.join("\n"), variables: Object.fromEntries(vars), instructionCount: inst.length };
  }
  function runTiny(bytes) {
    if (!Array.isArray(bytes) || bytes.length % 4 !== 0 || bytes.length > 1024 || bytes.some(x => !Number.isInteger(x) || x < 0 || x > 255)) throw Error("Bytecode phải là lệnh 4 byte hợp lệ");
    const regs = Array(8).fill(0), outputs = [], trace = [];
    let halted = false;
    for (let pc = 0; pc < bytes.length; pc += 4) {
      const [op, rd, a, b] = bytes.slice(pc, pc + 4);
      if (rd > 7 || a > 7 && op !== OPCODES.SET || b > 7) throw Error("Register index outside 0..7");
      let info = "";
      if (op === OPCODES.HALT) { halted = true; info = "HALT"; }
      else if (op === OPCODES.SET) {
        if (a > 2) throw Error("Invalid trit immediate");
        regs[rd] = a - 1; info = "SET R" + rd + "=" + regs[rd];
      } else if (op === OPCODES.TADD) {
        regs[rd] = wrap(regs[a] + regs[b]); info = "TADD R" + rd + "=" + regs[rd];
      } else if (op === OPCODES.TMUL) {
        regs[rd] = regs[a] * regs[b]; info = "TMUL R" + rd + "=" + regs[rd];
      } else if (op === OPCODES.EMIT) {
        outputs.push(regs[rd]); info = "EMIT " + regs[rd];
      } else throw Error("Unknown opcode " + op);
      trace.push({ pc: pc / 4, text: info, registers: regs.slice() });
      if (halted) break;
    }
    if (!halted) throw Error("Program missing HALT");
    return { registers: regs, outputs, trace };
  }

  // Synthetic and deterministic comparison; not trained weights or hardware timing.
  function simulateQuant(threshold = 0.3, seed = 20261110, rows = 8, cols = 16) {
    if (!Number.isFinite(threshold) || threshold < 0 || threshold > 1.5) throw Error("Threshold out of range");
    let state = seed >>> 0;
    function rand() {
      state ^= (state << 13); state ^= (state >>> 17); state ^= (state << 5);
      return (state >>> 0) / 4294967296;
    }
    const weights = Array.from({length: rows * cols}, () => (rand() * 2 - 1) * 1.25);
    const input = Array.from({length: cols}, () => rand() * 2 - 1);
    const q = weights.map(w => w > threshold ? 1 : (w < -threshold ? -1 : 0));
    const nonzero = q.filter(x => x !== 0).length;
    const scale = nonzero ? weights.reduce((sum, w, i) => sum + (q[i] ? Math.abs(w) : 0), 0) / nonzero : 0;
    const fp = [], tq = [];
    for (let r = 0; r < rows; r++) {
      let a = 0, b = 0;
      for (let c = 0; c < cols; c++) {
        a += weights[r * cols + c] * input[c];
        if (q[r * cols + c]) b += q[r * cols + c] * input[c];
      }
      fp.push(a); tq.push(b * scale);
    }
    const mse = fp.reduce((s, v, i) => s + (v - tq[i]) ** 2, 0) / rows;
    return {
      rows, cols, threshold, weights, quantized: q, input, fp, tq, nonzero,
      skipped: q.length - nonzero, scale, mse,
      fp32Bytes: q.length * 4, bytePack5: Math.ceil(q.length / 5),
      twoBitBytes: Math.ceil(q.length / 4)
    };
  }
  return Object.freeze({
    ALPHABET, OPCODES, indexToTrits, tritsToIndex, symbolToTrits, tritsToSymbol,
    encodeBase27, decodeBase27, balancedValue, balancedText, parseBalancedText,
    pack5, unpack5, byteHex, wrap, compileTiny, runTiny, simulateQuant
  });
});
