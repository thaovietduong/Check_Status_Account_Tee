#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_status.py — Kiểm tra hàng loạt trạng thái store trên TeePublic.

Đây là bản fork đơn giản hoá của tool GUI gốc (Tkinter). Bản này chạy bằng
dòng lệnh (CLI) để dễ đọc, dễ sửa, và dễ chạy tự động (không cần mở giao
diện đồ hoạ).

CÁCH DÙNG NHANH
----------------
    python check_status.py -i usernames.txt

    python check_status.py -i usernames.txt -p proxies.txt -w 15

Xem thêm chi tiết ở README.md và HANDOFF.md.

PHÂN LOẠI KẾT QUẢ
-----------------
Mỗi username được xếp vào đúng 1 trong 3 nhóm:

    1. acc_artist  -> Store đang hoạt động VÀ được Google index (title có
                       "T-Shirts by ..." và có thẻ <meta content="index, follow">).
                       Đây là các store "chính chủ", ổn định nhất.

    2. acc_thuong  -> Store vẫn tồn tại, trả về trang bình thường, nhưng
                       chưa/không thấy dấu hiệu được index như trên.

    3. acc_die     -> Store không còn tồn tại (404 / "Page Not Found"),
                       HOẶC không thể truy cập được do lỗi kết nối, timeout,
                       bị chặn proxy... (những trường hợp này được gộp vào
                       đây vì đều "đáng ngờ / cần bỏ qua hoặc kiểm tra lại",
                       nên đặt tên là acc_die (sus)).

Kết quả được ghi ra thư mục results/ với 4 file:
    - ket_qua_day_du_<timestamp>.txt   -> toàn bộ, kèm trạng thái chi tiết
    - acc_artist_<timestamp>.txt
    - acc_thuong_<timestamp>.txt
    - acc_die_sus_<timestamp>.txt
"""

import argparse
import csv
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Cấu hình mặc định — có thể chỉnh bằng tham số dòng lệnh, xem `--help`.
# ---------------------------------------------------------------------------
DEFAULT_WORKERS = 15          # số luồng chạy song song
DEFAULT_TIMEOUT = 10          # giây, timeout mỗi request
RESULTS_DIR = Path(__file__).resolve().parent / "results"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}


def load_usernames(path: Path) -> list[str]:
    """Đọc danh sách username từ file .txt (mỗi dòng 1 username) hoặc .csv
    (phải có cột 'username')."""
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if "username" not in (reader.fieldnames or []):
                sys.exit("Lỗi: file CSV phải có cột tên là 'username'.")
            return [row["username"].strip() for row in reader if row.get("username", "").strip()]
    else:
        with path.open(encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]


def load_proxies(path: Path | None) -> list[str]:
    if not path:
        return []
    with path.open(encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def format_proxy(raw_proxy: str) -> dict:
    """Hỗ trợ 2 định dạng:
        ip:port
        ip:port:user:pass
    """
    parts = raw_proxy.split(":")
    if len(parts) == 4:
        ip, port, user, pwd = parts
        proxy_url = f"http://{user}:{pwd}@{ip}:{port}"
    elif len(parts) == 2:
        ip, port = parts
        proxy_url = f"http://{ip}:{port}"
    else:
        raise ValueError(f"Không đọc được định dạng proxy: {raw_proxy}")
    return {"http": proxy_url, "https": proxy_url}


def classify(username: str, proxies: list[str], timeout: int) -> dict:
    """Gọi trang store trên TeePublic và trả về 1 dict:
        {username, url, raw_status, bucket}

    raw_status: "live" | "artist" | "die" | "error"  (trạng thái chi tiết)
    bucket:     "acc_artist" | "acc_thuong" | "acc_die_sus" (nhóm cuối cùng)
    """
    url = f"https://www.teepublic.com/user/{username}"

    proxy_dict = None
    if proxies:
        try:
            proxy_dict = format_proxy(random.choice(proxies))
        except ValueError as e:
            print(f"[warn] {e}")

    try:
        resp = requests.get(
            url, timeout=timeout, proxies=proxy_dict, headers=HEADERS, allow_redirects=True
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string.strip() if soup.title else ""

        if resp.status_code != 200 or "Page Not Found" in title:
            raw_status = "die"
        elif "T-Shirts by" in title:
            is_indexed = soup.find("meta", attrs={"content": "index, follow"}) is not None
            raw_status = "artist" if is_indexed else "live"
        else:
            raw_status = "live"

    except requests.RequestException as e:
        raw_status = "error"
        print(f"[error] {username}: {e}")

    bucket = {
        "artist": "acc_artist",
        "live": "acc_thuong",
        "die": "acc_die_sus",
        "error": "acc_die_sus",  # không truy cập được -> gộp vào die (sus)
    }[raw_status]

    return {"username": username, "url": url, "raw_status": raw_status, "bucket": bucket}


def run(usernames: list[str], proxies: list[str], workers: int, timeout: int) -> list[dict]:
    results = []
    total = len(usernames)
    done = 0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(classify, u, proxies, timeout): u for u in usernames}
        for future in as_completed(futures):
            username = futures[future]
            try:
                result = future.result()
            except Exception as e:  # an toàn: không để 1 lỗi làm hỏng cả job
                result = {"username": username, "url": "", "raw_status": "error", "bucket": "acc_die_sus"}
                print(f"[error] {username}: {e}")

            results.append(result)
            done += 1
            print(f"[{done}/{total}] {result['username']:<35} -> {result['bucket']}")

    return results


def save_results(results: list[dict]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    full_path = RESULTS_DIR / f"ket_qua_day_du_{ts}.txt"
    with full_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(f"{r['username']}|{r['raw_status']}|{r['bucket']}\n")

    bucket_files = {
        "acc_artist": RESULTS_DIR / f"acc_artist_{ts}.txt",
        "acc_thuong": RESULTS_DIR / f"acc_thuong_{ts}.txt",
        "acc_die_sus": RESULTS_DIR / f"acc_die_sus_{ts}.txt",
    }
    handles = {name: path.open("w", encoding="utf-8") for name, path in bucket_files.items()}
    counts = {name: 0 for name in bucket_files}
    try:
        for r in results:
            handles[r["bucket"]].write(f"{r['username']}\n")
            counts[r["bucket"]] += 1
    finally:
        for h in handles.values():
            h.close()

    print("\n===== TÓM TẮT =====")
    print(f"Tổng số check: {len(results)}")
    for name, path in bucket_files.items():
        print(f"  {name:<12}: {counts[name]:>5}  -> {path.name}")
    print(f"File đầy đủ   : {full_path.name}")
    print(f"Thư mục kết quả: {RESULTS_DIR}")


def parse_args():
    p = argparse.ArgumentParser(
        description="Kiểm tra hàng loạt trạng thái store TeePublic: artist / thường / die (sus)."
    )
    p.add_argument("-i", "--input", required=True, type=Path, help="File .txt hoặc .csv chứa danh sách username")
    p.add_argument("-p", "--proxies", type=Path, default=None, help="File .txt chứa danh sách proxy (tuỳ chọn)")
    p.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS, help=f"Số luồng song song (mặc định {DEFAULT_WORKERS})")
    p.add_argument("-t", "--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Timeout mỗi request, giây (mặc định {DEFAULT_TIMEOUT})")
    return p.parse_args()


def main():
    args = parse_args()

    if not args.input.exists():
        sys.exit(f"Không tìm thấy file input: {args.input}")

    usernames = load_usernames(args.input)
    if not usernames:
        sys.exit("File input không có username nào.")

    proxies = load_proxies(args.proxies)

    print(f"Đã nạp {len(usernames)} username" + (f", {len(proxies)} proxy." if proxies else " (không dùng proxy)."))
    start = time.time()

    results = run(usernames, proxies, args.workers, args.timeout)
    save_results(results)

    print(f"\nHoàn tất trong {time.time() - start:.1f} giây.")


if __name__ == "__main__":
    main()
