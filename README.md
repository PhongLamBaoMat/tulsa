# Tulsa

Bot thu nhặt tin tức về lĩnh vực an toàn thông tin (cyber security).

## Cài đặt môi trường phát triển

Tusla được viết bằng Python, phiên bản tối thiếu là 3.13 vì mã nguồn có sử dụng một vài tính năng mới chỉ có từ phiên bản 3.13.

### Python 3.13

Chúng tôi khuyến khích sử dụng [pyenv](https://github.com/pyenv/pyenv) để cài đặt Python 3.13. `pyenv` giúp tránh xung đột các phiên bản Python có sẵn ở trong máy.
```sh
pyenv install 3.13
pyenv global 3.13
```

### IDE hoặc text editor

Chúng tôi khuyến khích sử dụng [Zed](https://github.com/zed-industries/zed) hoặc [Visual Code](https://github.com/microsoft/vscode), đã được cài đặt [ruff](https://github.com/astral-sh/ruff) và [basedpyright](https://github.com/DetachHead/basedpyright).

- Zed mặc định đã có sẵn `ruff` và `basepyright`.
- Visual Code sử dụng Python extensions mặc định của Microsoft, bạn phải tự cài thêm 2 extensions `ruff` và `basepyright` và xoá những linters khác.

### Khởi tạo mã nguồn
Tải mã nguồn
```sh
git clone https://github.com/PhongLamBaoMat/tulsa
```

Dự án sử dụng [uv](https://github.com/astral-sh/uv) để quản lý các thư viện dùng trong dự án. Bạn cần `uv` để tải các thư viện này.
```sh
cd tulsa
uv sync
```

Như vậy bạn đã hoàn thành quá trình cài đặt môi trường phát triển.
