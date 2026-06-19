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
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )

        date_str = datetime.now().strftime("%Y%m%d_%H%M")

        for name, url in urls.items():
            print(f"Đang xử lý {name}: {url}")
            page = await context.new_page()

            try:
                # 1. Tải trang với cấu trúc DOM sẵn sàng
                await page.goto(
                    url, wait_until="domcontentloaded", timeout=60000
                )
                await page.wait_for_timeout(15000)  # Đợi 15s cho dữ liệu đổ về hết

                # 2. CHÂN THỰC HÓA LAZY LOADING: Cuộn xuống cuối trang để ép web tải hết các tháng kỳ hạn xa
                await page.evaluate(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                await page.wait_for_timeout(3000)
                await page.evaluate("window.scrollTo(0, 0);")
                await page.wait_for_timeout(1000)

                # 3. ÉP GIÃN BẢNG (Bẻ gãy thuộc tính overflow gây cắt cụt hàng)
                # Giữ nguyên tiêu đề và ngày "Data as of...", chỉ ẩn thanh menu điều hướng quảng cáo phía trên cùng
                await page.add_style_tag(
                    content="""
                    header.cmeHeader, .col-md-3.sidebar, .cmeFooter, .cookie-consent { 
                        display: none !important; 
                    }
                    html, body, .main-content, .cmeTable-wrapper, [class*="wrapper"], [class*="container"] {
                        overflow: visible !important;
                        max-height: none !important;
                        height: auto !important;
                    }
                """
                )

                # 4. Chuyển sang chế độ hiển thị để in ấn (Print Media)
                await page.emulate_media(media="print")

                file_name = f"CME_{name}_Settlements_{date_str}.pdf"

                # 5. Xuất định dạng PDF khổ Ngang chuẩn Audit
                await page.pdf(
                    path=file_name,
                    format="A4",
                    print_background=True,
                    display_header_footer=True,
                    scale=0.85,  # Thu nhỏ nhẹ về 85% để các cột Open, High, Low, Settle vừa vặn khổ ngang
                    landscape=True,  # Bắt buộc để khổ ngang cho bảng biểu tài chính
                    margin={
                        "top": "15mm",
                        "bottom": "15mm",
                        "left": "12mm",
                        "right": "12mm",
                    },
                )
                print(f"-> Đã lưu thành công: {file_name}")

            except Exception as e:
                print(f"-> Lỗi khi xử lý {name}: {e}")

            finally:
                await page.close()

        await browser.close()


if __name__ == "__main__":
    asyncio.run(save_cme_to_pdf())
