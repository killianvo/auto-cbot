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
        browser = await p.chromium.launch(headless=False, args=["--headless=new"])
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
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)

                # Đợi 12 giây để bảng giá tải xong hoàn toàn
                await page.wait_for_timeout(12000)

                file_name = f"CME_{name}_Settlements_{date_str}.pdf"

                # Xuất PDF có lề và có URL ở chân trang phục vụ Audit
                await page.pdf(
                    path=file_name,
                    format="A4",
                    print_background=True,
                    display_header_footer=True,
                )
                print(f"-> Đã lưu: {file_name}")

            except Exception as e:
                print(f"-> Lỗi tải {name}: {e}")

            finally:
                await page.close()

        await browser.close()


if __name__ == "__main__":
    asyncio.run(save_cme_to_pdf())
