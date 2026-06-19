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
        browser = await p.chromium.launch(
            headless=False, args=["--headless=new"]
        )
        # Giả lập trình duyệt chuẩn để không bị CME chặn
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

                # Đợi 15 giây để bảng giá tải ổn định dữ liệu từ API về
                await page.wait_for_timeout(15000)

                # KỸ THUẬT 1: Giả lập cuộn chuột xuống đáy trang để kích hoạt load hết các tháng kỳ hạn xa
                await page.evaluate(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                await page.wait_for_timeout(3000)
                await page.evaluate("window.scrollTo(0, 0);")
                await page.wait_for_timeout(1000)

                # KỸ THUẬT 2: Tiêm mã CSS để phá vỡ khung cuộn, ép bảng giãn dài tự nhiên theo số dòng
                # Chỉ ẩn thanh menu quảng cáo trên cùng (cmeHeader) và footer, GIỮ LẠI tiêu đề chứa ngày Trade Date
                await page.add_style_tag(
                    content="""
                    header.cmeHeader, .col-md-3.sidebar, .cmeFooter, .cookie-consent, #onetrust-banner-sdk { 
                        display: none !important; 
                    }
                    html, body, .main-content, .cmeTable-wrapper, [class*="wrapper"], [class*="container"], [class*="table-responsive"] {
                        overflow: visible !important;
                        max-height: none !important;
                        height: auto !important;
                    }
                    .cmeTable {
                        width: 100% !important;
                    }
                """
                )

                # Chuyển chế độ hiển thị sang dạng bản in (Print Media)
                await page.emulate_media(media="print")

                file_name = f"CME_{name}_Settlements_{date_str}.pdf"

                # KỸ THUẬT 3: Tối ưu hóa các thông số PDF cho báo cáo tài chính rộng nhiều cột
                await page.pdf(
                    path=file_name,
                    format="A4",
                    print_background=True,
                    display_header_footer=True,  # Hiển thị URL và số trang ở rìa giấy

                    # Tỷ lệ 85% kết hợp khổ Ngang (Landscape) giúp hiển thị trọn vẹn từ Open đến Settle/Open Interest
                    scale=0.85,
                    landscape=True,

                    # Đổi lề sang đơn vị mm chuẩn in ấn, giúp bảng cân đối và không bị rúc sát viền
                    margin={
                        "top": "15mm",
                        "bottom": "15mm",
                        "left": "12mm",
                        "right": "12mm",
                    },
                )
                print(f"-> Đã lưu: {file_name}")

            except Exception as e:
                print(f"-> Lỗi tải {name}: {e}")

            finally:
                await page.close()

        await browser.close()


if __name__ == "__main__":
    asyncio.run(save_cme_to_pdf())
