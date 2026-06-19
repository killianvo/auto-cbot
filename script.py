import asyncio
import os
from datetime import datetime

from playwright.async_api import async_playwright


async def save_cme_to_pdf():
    # Danh sách 3 đường link hàng hóa bạn cần
    urls = {
        "Corn": "https://www.cmegroup.com/markets/agriculture/grains/corn/settlements",
        "Soybean_Meal": "https://www.cmegroup.com/markets/agriculture/oilseeds/soybean-meal/settlements",
        "Wheat": "https://www.cmegroup.com/markets/agriculture/grains/wheat/settlements",
    }

    async with async_playwright() as p:
        # GIỮ NGUYÊN dòng launch này vì nó giúp bypass Cloudflare trên GitHub Actions thành công
        browser = await p.chromium.launch(
            headless=False, args=["--headless=new"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )

        date_str = datetime.now().strftime("%Y%m%d_%H%M")

        # Lặp qua từng link để chụp PDF
        for name, url in urls.items():
            print(f"Đang xử lý {name}: {url}")
            page = await context.new_page()

            try:
                await page.goto(
                    url, wait_until="domcontentloaded", timeout=60000
                )
                # Chờ 12 giây để bảng giá tải xong dữ liệu ban đầu
                await page.wait_for_timeout(12000)

                # 1. Cuộn xuống đáy để kích hoạt tải (lazy load) các tháng tương lai xa
                await page.evaluate(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                await page.wait_for_timeout(3000)
                await page.evaluate("window.scrollTo(0, 0);")
                await page.wait_for_timeout(1000)

                # 2. Thực thi Javascript dọn dẹp giao diện và bẻ gãy khung cuộn gây cắt hàng
                await page.evaluate("""() => {
                    // Tự động bấm nút Chấp nhận Cookie nếu có để dọn sạch màn hình
                    const cookieBtn = document.querySelector('#onetrust-accept-btn-handler');
                    if (cookieBtn) cookieBtn.click();

                    // Ẩn menu quảng cáo và footer, GIỮ LẠI tiêu đề chứa ngày Trade Date ("Data as of...")
                    const elementsToHide = [
                        'header.cmeHeader', 
                        '.cmeFooter', 
                        '#onetrust-banner-sdk', 
                        '#onetrust-consent-sdk',
                        '.cookie-consent',
                        '.modal-backdrop',
                        '.parbase.banner'
                    ];
                    elementsToHide.forEach(selector => {
                        const el = document.querySelector(selector);
                        if (el) el.style.setProperty('display', 'none', 'important');
                    });

                    // SỬA LỖI CẮT HÀNG (Future Months): Ép các khung cuộn chứa bảng phải hiển thị tràn trang tự nhiên
                    const wrappers = document.querySelectorAll('.cmeTable-wrapper, .table-responsive, .main-content');
                    wrappers.forEach(el => {
                        el.style.setProperty('overflow', 'visible', 'important');
                        el.style.setProperty('max-height', 'none', 'important');
                        el.style.setProperty('height', 'auto', 'important');
                    });

                    document.body.style.setProperty('overflow', 'visible', 'important');
                    document.body.style.setProperty('height', 'auto', 'important');
                }""")

                # Chờ thêm 2 giây để giao diện cập nhật sau khi chạy JS ổn định layout
                await page.wait_for_timeout(2000)

                file_name = f"CME_{name}_Settlements_{date_str}.pdf"

                # 3. Xuất file PDF khổ ngang sắc nét phục vụ kiểm toán
                await page.pdf(
                    path=file_name,
                    format="A4",
                    print_background=True,
                    display_header_footer=True,
                    scale=0.85,  # Thu nhỏ nhẹ về 85% để các cột Open, High, Low, Settle vừa vặn khổ ngang
                    landscape=True,  # Khổ ngang cực kỳ lý tưởng cho bảng biểu tài chính rộng nhiều cột
                    margin={
                        "top": "40px",
                        "bottom": "40px",
                        "left": "20px",
                        "right": "20px",
                    },
                )
                print(f"-> Đã lưu thành công: {file_name}")

            except Exception as e:
                print(f"-> Lỗi tải {name}: {e}")

            finally:
                await page.close()

        await browser.close()


if __name__ == "__main__":
    asyncio.run(save_cme_to_pdf())
