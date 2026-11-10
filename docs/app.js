/* Ternary Eco interactive web workbench. No network, no eval, no telemetry. */
(function() {
  "use strict";
  const C = window.TernaryCore;
  const V = window.CVNSSConverter;
  const $ = id => document.getElementById(id);
  const set = (id, text) => { const e = $(id); if (e) e.textContent = String(text); };
  const vi = n => Number(n).toLocaleString("vi-VN", {maximumFractionDigits: 4});
  const err = e => e instanceof Error ? e.message : String(e);

  function setupTabs() {
    const tabs = Array.from(document.querySelectorAll(".tab[data-tab]"));
    for (const tab of tabs) tab.addEventListener("click", () => {
      for (const other of tabs) {
        const active = other === tab;
        other.classList.toggle("active", active);
        other.setAttribute("aria-selected", active ? "true" : "false");
        other.tabIndex = active ? 0 : -1;
        const panel = $("panel-" + other.dataset.tab);
        panel.hidden = !active;
        panel.classList.toggle("active", active);
      }
    });
    tabs.forEach((tab, index) => tab.addEventListener("keydown", e => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(e.key)) return;
      e.preventDefault();
      const next = e.key === "Home" ? 0 : e.key === "End" ? tabs.length - 1 :
        (index + (e.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
      tabs[next].focus(); tabs[next].click();
    }));
  }

  function renderSymbols(symbols) {
    const tbody = $("symbolRows"); tbody.replaceChildren();
    for (const ch of symbols.slice(0, 80)) {
      const d = C.symbolToTrits(ch);
      const bal = d.map(x => x - 1);
      const row = document.createElement("tr");
      for (const text of [ch === " " ? "␠ SPACE" : ch, String(C.ALPHABET.indexOf(ch)), d.join(""),
        C.balancedText(bal), String(C.balancedValue(bal))]) {
        const td = document.createElement("td"); td.textContent = text; row.appendChild(td);
      }
      tbody.appendChild(row);
    }
  }

  function convertVietnamese() {
    try {
      if (!V) throw Error("Chưa tải được CVNSS converter v5.");
      const input = $("vnInput").value.normalize("NFC");
      if (!input) throw Error("Hãy nhập văn bản tiếng Việt.");
      const result = V.fromCqn(input);
      const code = result.cvss;
      const base = code.toUpperCase();
      const trits = C.encodeBase27(base);
      const reconstructedCode = C.decodeBase27(trits);
      const decoded = V.fromCvss(code).cqn;
      if (reconstructedCode !== base) throw Error("Base27 self-check mismatch");
      set("cvssOutput", code.replace(/ /g, " ␠ "));
      set("tritOutput", trits.join("").replace(/(.{3})/g, "$1 ").trim());
      set("reverseOutput", decoded);
      set("conversionStatus", "ĐÃ MÃ HÓA");
      const exact = input === decoded;
      set("conversionDetails", code.length + " ký hiệu → " + trits.length + " trit → " +
        Math.ceil(trits.length / 5) + " byte pack5 (lý thuyết) · " +
        (exact ? "Khôi phục đúng câu mẫu." : "Bản giải mã canonical khác bản gốc; cần giữ ngữ cảnh/metadata để lossless."));
      renderSymbols(Array.from(base));
    } catch (e) {
      set("conversionStatus", "KHÔNG HỢP LỆ");
      set("conversionDetails", err(e));
      set("cvssOutput", "—"); set("tritOutput", "—"); set("reverseOutput", "—");
      $("symbolRows").replaceChildren();
    }
  }

  function inspect() {
    try {
      if (!V) throw Error("Chưa có CVNSS converter.");
      const word = $("inspectInput").value.trim();
      if (!word) throw Error("Nhập mã CVNSS cần tra.");
      const r = V.inspectWord(word, "cvss");
      set("inspectResult", "Mã: " + r.codeVowel + " · " + (r.ambiguous ? "NHẬP NHẰNG" : "Một chính sách giải mã") +
        (r.critical ? " · va chạm trọng yếu" : "") + "\nỨng viên: " + r.candidates.join(" | ") +
        "\nMặc định: " + r.selected);
      $("inspectResult").classList.remove("error");
    } catch (e) {
      set("inspectResult", err(e)); $("inspectResult").classList.add("error");
    }
  }

  function pack() {
    try {
      const raw = $("packInput").value.replace(/\s+/g, "");
      const t = C.parseBalancedText(raw);
      const bytes = C.pack5(t);
      const unpacked = C.unpack5(bytes, t.length);
      if (C.balancedText(unpacked) !== C.balancedText(t)) throw Error("Round-trip mismatch");
      set("packOutput", C.byteHex(bytes));
      set("unpackOutput", C.balancedText(unpacked).replace(/(.{5})/g, "$1 "));
      const twoBitBytes = Math.ceil(t.length / 4);
      set("packMetrics", t.length + " trit · " + bytes.length + " byte pack5 · " +
        twoBitBytes + " byte 2-bit/trit · dữ liệu tháo gói giống 100%. " +
        "Hiệu suất mã 5·log₂(3)/8 = 99,06% giới hạn Shannon mỗi byte; không tính metadata.");
      $("packMetrics").classList.remove("error");
    } catch (e) {
      set("packOutput", "—"); set("unpackOutput", "—");
      set("packMetrics", err(e)); $("packMetrics").classList.add("error");
    }
  }

  function compile() {
    try {
      const program = C.compileTiny($("tinyInput").value);
      const result = C.runTiny(program.bytes);
      set("asmOutput", program.asm);
      set("bytecodeOutput", C.byteHex(program.bytes));
      set("vmOutput", result.trace.map(s => "PC " + String(s.pc).padStart(2,"0") +
        " │ " + s.text.padEnd(12," ") + " │ [" + s.registers.join(", ") + "]").join("\n"));
      set("compilerStatus", program.instructionCount + " lệnh · " + program.bytes.length +
        " byte mã máy GIẢ LẬP · output = [" + result.outputs.join(", ") +
        "]. Không chạy mã JS tùy ý / không phát sinh firmware.");
      $("compilerStatus").classList.remove("error");
    } catch (e) {
      set("asmOutput","—");set("bytecodeOutput","—");set("vmOutput","—");
      set("compilerStatus",err(e)); $("compilerStatus").classList.add("error");
    }
  }

  function quantize() {
    try {
      const threshold = Number($("thresholdInput").value);
      set("thresholdValue", threshold.toLocaleString("vi-VN",{minimumFractionDigits:2,maximumFractionDigits:2}));
      const r = C.simulateQuant(threshold);
      const total = r.quantized.length;
      set("sparsityVal", vi(100 * r.skipped / total) + "%");
      set("floatBytes", vi(r.fp32Bytes) + " B");
      set("ternaryBytes", vi(r.bytePack5) + " B");
      set("mseVal", r.mse.toFixed(4));
      const scale = Math.max(0.01, ...r.fp.map(Math.abs), ...r.tq.map(Math.abs));
      const chart = $("quantBars"); chart.replaceChildren();
      for (let i = 0; i < r.rows; i++) {
        const group = document.createElement("div"); group.className = "bar-group";
        const area = document.createElement("div"); area.className = "bar-viz";
        for (const [name, value] of [["bar-float",r.fp[i]],["bar-tern",r.tq[i]]]) {
          const bar = document.createElement("i"); bar.className = name + (value < 0 ? " negative" : "");
          bar.style.height = Math.max(1, Math.abs(value) / scale * 46) + "%";
          bar.title = (name === "bar-float" ? "FP32: " : "Trit: ") + value.toFixed(4);
          area.appendChild(bar);
        }
        const label = document.createElement("small"); label.textContent = "Y" + i;
        group.append(area, label); chart.appendChild(group);
      }
    } catch (e) { set("mseVal", "ERR"); $("quantBars").textContent = err(e); }
  }

  const targets = {
    esp: {
      title: "ESP32‑S3 / Xtensa LX7",
      notes: "ESP32‑S3 sử dụng kiến trúc nhị phân. Đầu vào là trọng số trit {-1,0,+1} lưu trong int8 hoặc pack5; nạp vào firmware ESP‑IDF rồi đo chu kỳ/PSRAM/điện năng. Mẫu C dưới đây là kernel tham chiếu, chưa được flash hoặc benchmark.",
      code: [
        "#include <stdint.h>",
        "#include <stddef.h>",
        "// x: vector int16_t, w: trits in {-1,0,+1}.",
        "// int32 accumulator; choose bounds to avoid overflow.",
        "int32_t ternary_dot(const int16_t *x,",
        "                    const int8_t *w, size_t n) {",
        "  int32_t sum = 0;",
        "  for (size_t i = 0; i < n; ++i) {",
        "    if (w[i] == 1) sum += x[i];",
        "    else if (w[i] == -1) sum -= x[i];",
        "  }",
        "  return sum;",
        "}",
        "// Pack5 decode / alignment / scaling not shown."
      ].join("\n")
    },
    fpga: {
      title: "NHDL / VHDL‑2008 / FPGA",
      notes: "Biên dịch trạng thái tam phân thành mã hóa 2-bit signed trong FPGA nhị phân. Mạch phải được kiểm chứng bằng golden vector, GHDL, tổng hợp, timing và báo cáo LUT/FF/DSP. Ví dụ là cộng modulo 3, KHÔNG phải cộng số nguyên có carry.",
      code: [
        "library ieee;",
        "use ieee.std_logic_1164.all;",
        "use ieee.numeric_std.all;",
        "entity trit_add is",
        "  port(a,b: in signed(1 downto 0);",
        "       y: out signed(1 downto 0));",
        "end entity;",
        "architecture rtl of trit_add is",
        "begin",
        "  process(a,b)",
        "    variable s: integer;",
        "  begin",
        "    s := to_integer(a) + to_integer(b);",
        "    if s > 1 then s := s - 3; end if;",
        "    if s < -1 then s := s + 3; end if;",
        "    y <= to_signed(s, 2);",
        "  end process;",
        "end architecture;",
        "-- Input code 2'b10 (-2) is invalid: validate upstream."
      ].join("\n")
    },
    browser: {
      title: "Browser VM / JavaScript",
      notes: "Đây là backend đã chạy trong trang này. Parser BilaTiny chỉ nhận cú pháp tĩnh được định nghĩa, không dùng eval hoặc gửi dữ liệu ra mạng. Bytecode 4 byte/lệnh là đặc tả giáo dục do Ternary Eco xác định.",
      code: [
        "const program = TernaryCore.compileTiny(",
        "  'trit a = +1; trit b = -1; ' +",
        "  'trit c = tadd(a,b); emit(c);'",
        ");",
        "console.log(TernaryCore.byteHex(program.bytes));",
        "console.log(TernaryCore.runTiny(program.bytes));",
        "// Not ESP32 machine code and not VHDL."
      ].join("\n")
    }
  };
  function setTarget() {
    const key = $("targetSelect").value, t = targets[key];
    set("targetTitle",t.title);set("targetNotes",t.notes);set("targetCode",t.code);
  }
  function manifest() {
    const key = $("targetSelect").value;
    const m = {
      project: "Ternary Eco Lab", version: "0.1.0-research",
      date: "2026-11-10", target: key,
      converter: V ? V.VERSION : null, alphabet: C.ALPHABET,
      trits: [-1,0,1], packing: "5 balanced trits / 8-bit byte",
      compiler: "BilaTiny typed educational subset",
      bytecode: "4 bytes per instruction; educational VM; not device ISA",
      quantization: {type:"synthetic",seed:20261110,threshold:Number($("thresholdInput").value)},
      verified: {browser: true, esp32s3: false, fpga: false, trainedTinyLLM: false},
      cautions: [
        "CVNSS conversion can be many-to-one; store context/metadata for fully lossless original text.",
        "This manifest does not contain executable firmware, FPGA bitstream or trained LLM weights."
      ]
    };
    const blob = new Blob([JSON.stringify(m,null,2)],{type:"application/json"});
    const url = URL.createObjectURL(blob), a = document.createElement("a");
    a.href=url;a.download="ternary-eco-"+key+"-manifest.json";document.body.appendChild(a);
    a.click();a.remove();setTimeout(() => URL.revokeObjectURL(url),1000);
  }

  function selfTests() {
    const checks = [], failed = [];
    const check = (name, test) => {
      try { if (!test()) throw Error("Không khớp"); checks.push(name); }
      catch (e) { failed.push(name + ": " + err(e)); }
    };
    check("CVNSS v5 audit-safe selfTest()",() => !!V && V.selfTest().ok);
    check("56 nhóm ambiguity · 5 critical",() => !!V && V.audit().ambiguityGroups === 56 && V.audit().criticalCollisionGroups === 5);
    check("Base27 27/27 ký hiệu",() => {
      for (let i=0;i<27;i++) if (C.tritsToIndex(C.indexToTrits(i))!==i) return false; return true;
    });
    check("Base27 ↔ trit round-trip",() => C.decodeBase27(C.encodeBase27("VIET NAM")) === "VIET NAM");
    check("5-trit byte pack/unpack",() => {
      for (let n=1;n<70;n++) {
        const arr=Array.from({length:n},(_,i)=>i%3-1);
        if (C.balancedText(C.unpack5(C.pack5(arr),n))!==C.balancedText(arr)) return false;
      } return true;
    });
    check("BilaTiny compiler / VM",() => {
      const p=C.compileTiny("trit x = +1; trit y = +1; trit z = tadd(x,y); emit(z);");
      return C.runTiny(p.bytes).outputs[0]===-1;
    });
    check("Ternary quant deterministic",() => {
      const a=C.simulateQuant(0.35),b=C.simulateQuant(0.35);
      return JSON.stringify(a.tq)===JSON.stringify(b.tq) && a.skipped+a.nonzero===128;
    });
    const summary=checks.length+" / "+(checks.length+failed.length)+" bài kiểm chứng đạt" +
      (failed.length?" · có lỗi":" · self-test pass");
    set("testSummary",summary);
    set("testResults",failed.length?failed.join("\n"):"✓ "+checks.join("   •   "));
    $("testResults").style.color=failed.length?"#ff9b9b":"#c5f179";
  }

  function init() {
    if (!C) { set("testSummary", "Không thể tải core.js"); return; }
    setupTabs();
    $("convertBtn").addEventListener("click",convertVietnamese);
    const samples=["Xin chào Việt Nam","Tôi yêu tiếng Việt","Trí tuệ nhân tạo"];
    let idx=0;
    $("sampleBtn").addEventListener("click",()=>{$("vnInput").value=samples[++idx%samples.length];convertVietnamese();});
    $("inspectBtn").addEventListener("click",inspect);
    $("packBtn").addEventListener("click",pack);
    $("compileBtn").addEventListener("click",compile);
    $("resetCodeBtn").addEventListener("click",()=>{
      $("tinyInput").value="trit a = +1;\ntrit b = +1;\ntrit c = tadd(a, b);\ntrit d = tmul(c, a);\nemit(c);\nemit(d);";
      compile();
    });
    $("thresholdInput").addEventListener("input",quantize);
    $("quantBtn").addEventListener("click",quantize);
    $("targetSelect").addEventListener("change",setTarget);
    $("manifestBtn").addEventListener("click",manifest);
    $("testBtn").addEventListener("click",selfTests);
    convertVietnamese();inspect();pack();compile();quantize();setTarget();selfTests();
  }
  document.addEventListener("DOMContentLoaded",init);
})();
