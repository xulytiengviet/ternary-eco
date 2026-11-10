# Ternary Eco Lab — Reproducibility

Ngày cập nhật: 2026-11-10. Nền tảng: HTML/CSS/JavaScript tĩnh; Node.js 22 để kiểm thử.

## 1. Mục tiêu và phạm vi

Repository vẫn giữ nguyên mã Python TriCPU, TriAsm, TriLang, TriOS và thư viện gốc từ dự án theeteeshrimp/ternary-ecosystem. Phần mới nằm trong thư mục docs:

- CVNSS4.0 v5.0.0-audit-safe từ tệp được cung cấp, gồm 56 chính sách canonical xử lý mã nhập nhằng.
- Base27 với SPACE + A–Z = 27 ký hiệu; mỗi ký hiệu ánh xạ thành 3 chữ số cơ số 3. Dịch từng chữ số 0/1/2 thành trit cân bằng −1/0/+1 cho giá trị trong khoảng −13 đến +13.
- Đóng gói 5 trit vào 1 byte; lưu độ dài gốc để tháo gói chuẩn. Vì 3^5=243, các giá trị byte 243..255 không hợp lệ.
- BilaTiny subset, một ngữ pháp nhỏ có kiểu trit, chuyển thành bytecode minh họa 4 byte/lệnh và chạy trên VM 8 thanh ghi. Không phải compiler BilaScript hoàn chỉnh.
- Mô phỏng ma trận trọng số tổng hợp 8×16 với seed cố định; đối chiếu FP32 với lượng tử hóa {-1,0,+1} có scale chung. Không phải TinyLLM đã được huấn luyện.

## 2. Chạy trang web

Dùng Python hoặc bất kỳ static server:

    python -m http.server 8000

Mở http://localhost:8000/docs/ hoặc mở trực tiếp docs/index.html trên trình duyệt. Ứng dụng không cần API server và không truyền dữ liệu đầu vào đi nơi khác.

## 3. Kiểm thử Node.js

    node --test tests/lab.test.cjs

Bộ kiểm thử gồm 23 self-test của CVNSS v5, 27 trạng thái Base27, các chiều dài pack5 từ 0 đến 102, phép cộng và nhân Z3, compiler/VM và phép thử lượng tử hóa tái lập. GitHub Actions chạy cùng câu lệnh này khi mã docs/tests thay đổi.

Các ví dụ chạy riêng mã Python nền (KHÔNG phải engine mà trang web gọi):

    python emulator/tri_cpu.py
    python assembler/tri_asm.py examples/factorial.asm --run
    python compiler/trilang.py examples/hello.tri --asm --run
    python os/trios.py
    python stdlib/tri_stdlib.py

Các lệnh Python thuộc dự án gốc, chưa nằm trong Node CI.

## 4. Hợp đồng biểu diễn dữ liệu

1. CVNSS v5 chuyển đổi theo chính sách canonical; mã nhiều-một có thể không khôi phục đúng mọi văn bản đầu vào. Muốn lossless cần lưu ngữ cảnh/metadata. Các ký tự ngoài A–Z và SPACE sau bước CVNSS sẽ bị báo lỗi, không lặng lẽ bỏ đi.
2. Ba chữ số base-3 0/1/2 được đổi từng vị trí thành ba trit cân bằng T/0/1, với T=−1. Đây là hai cách biểu diễn khác nhau của cùng chỉ số ký hiệu.
3. Pack5 lưu năm trit cân bằng/byte với quy tắc padding trit 0 phía phải; cần lưu độ dài trước padding. Mục tiêu là mã hóa dữ liệu chứ không phải lệnh ALU.
4. BilaTiny demo có lệnh SET/TADD/TMUL/EMIT/HALT, opcode 4 byte/lệnh do dự án xác định. TADD là cộng modulo 3 và không phải cộng số nguyên có carry. Pseudo-ISA này không đồng nhất với TriCPU Python hoặc ISA Xtensa.
5. Inference sử dụng đầu vào và trọng số nhân tạo có seed cố định, ngưỡng, scale chung, MSE và số byte trọng số; không suy ra độ chính xác mô hình, hiệu suất thiết bị hoặc tiết kiệm điện.

## 5. Các cổng kiểm chứng phần cứng và AI

ESP32-S3: cần triển khai codec/quantized kernel bằng C hoặc Rust, cross-compile với ESP-IDF, kiểm golden vector, đo flash/IRAM/PSRAM, cycle, latency, năng lượng và accuracy trên tập kiểm thử có nguồn gốc.

FPGA: cần định nghĩa mã hóa trit 2-bit cùng chính sách trạng thái bất hợp lệ, sinh VHDL-2008, chạy GHDL và testbench đầy đủ chín tổ hợp đầu vào, sau đó tổng hợp trên bo xác định và báo cáo LUT/FF/DSP/fmax/timing/power.

TinyLLM/BilaTiny: cần tokenizer và corpus tiếng Việt có provenance, checkpoint huấn luyện, quantization scale, perplexity/accuracy trên held-out set, đối chiếu chất lượng và đo phần cứng. Base27 của chữ viết không thay thế tokenizer của mô hình ngôn ngữ.

## 6. Attribution & giấy phép

- Python baseline: https://github.com/theeteeshrimp/ternary-ecosystem (MIT); README và LICENSE gốc vẫn được giữ.
- SuperInstance ternary-inference-sim: https://github.com/SuperInstance/ternary-inference-sim (MIT); tham khảo TritPack, Z3, inference, không sao chép mã Rust sang trang.
- RFI-IRFOS Ternary Intelligence Stack: https://github.com/rfi-irfos/ternary-intelligence-stack (mã giấy phép hỗn hợp LGPL-3.0 / BSL-1.1 theo README); chỉ liên kết, không vendor.
- Rusty Penguin: https://github.com/rfi-irfos/rusty-penguin; ví dụ tích hợp logic tam phân trên OS nhị phân.
- Trilang: https://github.com/trilang/trilang; ví dụ cấu trúc compiler .NET/C#.
- HN thảo luận pack5: https://hn.nuxt.dev/item/48912812.
- OSDev https://forum.osdev.org/viewtopic.php?p=354532 và Zenodo https://zenodo.org/records/21894461 là URL do người dùng cung cấp; chưa kiểm chứng được nội dung nguồn ở thời điểm tích hợp.
- Tệp docs/assets/cvnss-converter.js được cung cấp để tích hợp vào dự án; giữ nguyên API và ghi chú bản gốc. Cần rà soát quyền cấp phép trước khi tái sử dụng rộng rãi.

## 7. Diễn giải đúng CI

CI xanh chỉ chứng minh thuật toán tham chiếu trong môi trường Node.js phù hợp với các ca kiểm thử. CI xanh không chứng minh chip tam phân vật lý, firmware ESP32-S3, FPGA đã chạy, hoặc TinyLLM thực được huấn luyện. Ngưỡng tái lập 98% (nếu áp dụng) phải có chỉ số, bộ dữ liệu đóng băng và chuẩn so sánh độc lập.
