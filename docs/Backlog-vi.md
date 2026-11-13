# Backlog

## [Thấp] Kiểu chữ và kiểu phụ đề AI Video Studio chưa port được

Gói `text-styles/` chỉ giữ phần tĩnh viết được bằng schema `text-style`/`subtitle-style` hiện có. Các kiểu dưới đây bị bỏ vì cần thứ editor chưa có; làm được khi editor có shader chữ, hạt, texture, blend hoặc chuyển động theo từng ký tự.

- Kiểu chữ `Đánh máy` (`type`) và `Lật chữ` (`tumble`): phần đáng giá là hiệu ứng theo từng ký tự; chỉ giữ màu thì tên kiểu gây hiểu nhầm.
- Kiểu phụ đề HyperFrames: `hf_glitch_rgb` (tách kênh RGB, scanline), `hf_particle_burst` (nổ hạt), `hf_matrix_decode` (xáo ký tự), `hf_blend_difference` (mix-blend difference), `hf_texture` (tô texture), `hf_parallax_layers` (nhiều lớp chữ trôi).
- `bc_holo` (tấm HUD, góc chéo, vạch âm thanh động) và `multicam` (màu theo người nói).
- Phần động của các kiểu đã port: gradient chữ (`hf_gradient_fill`, nền gradient của `transform`), emoji bật (`hf_emoji_pop`), từ đập từng từ (`hf_kinetic_slam`), lau chữ (`hf_clip_wipe`), đổi độ đậm (`hf_weight_shift`), hai cỡ chữ trong một clip (`print_kdoc`, `mt_result`, `ex_pp`, `hf_editorial_emphasis`). Mục `karaoke` của từng kiểu đã ghi sẵn thông số cho lúc editor vẽ được.
