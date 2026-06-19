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
            headless=True, args=["--headless=new"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )

        date_str = datetime.now().strftime("%Y%m%d_%H%M")

        for name, url in urls.items():
            print(f"Đang xử lý {name}: {url}")
            page = await context.new_page()

            try:
                await page.goto(
                    url, wait_until="domcontentloaded", timeout=60000
                )

                # Đợi 15 giây để bảng giá tải ổn định dữ liệu
                await page.wait_for_timeout(15000)

                # === BƯỚC MỚI 1: CHỦ ĐỘNG BẤM NÚT ACCEPT COOKIE NẾU XUẤT HIỆN ===
                try:
                    cookie_button = page.locator("#onetrust-accept-btn-handler")
                    if await cookie_button.is_visible():
                        await cookie_button.click(timeout=3000)
                        print(f"-> Đã bấm tắt bảng Cookie của {name}")
                        await page.wait_for_timeout(
                            1000
                        )  # Đợi 1s cho hiệu ứng biến mất hẳn
                except Exception as e:
                    print(f"-> Không thấy nút Cookie hoặc lỗi bấm: {e}")

                # Giả lập cuộn chuột xuống đáy trang để kích hoạt load hết các tháng kỳ hạn xa
                await page.evaluate(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                await page.wait_for_timeout(3000)
                await page.evaluate("window.scrollTo(0, 0);")
                await page.wait_for_timeout(1000)

                # === BƯỚC MỚI 2: TIÊM CSS XÓA BỎ HOÀN TOÀN CÁC LỚP PHỦ MỜ VÀ QUẢNG CÁO ===
                await page.add_style_tag(
                    content="""
                    /* 1. Ẩn menu, footer, banner cookie và tất cả các loại popup/modal quảng cáo phát sinh */
                    header.cmeHeader, .col-md-3.sidebar, .cmeFooter, .cookie-consent, 
                    #onetrust-banner-sdk, #onetrust-consent-sdk, .onetrust-pc-dark-filter,
                    [id*="onetrust"], [class*="modal-backdrop"], [class*="popup"], .parbase.banner { 
                        display: none !important; 
                        visibility: hidden !important;
                    }
                    
                    /* 2. Ép bảng giãn dài tự nhiên theo số dòng */
                    html, body, .main-content, .cmeTable-wrapper, [class*="wrapper"], [class*="container"], [class*="table-responsive"] {
                        overflow: visible !important;
                        max-height: none !important;
                        height: auto !important;
                    }
                    
                    /* 3. QUAN TRỌNG: Mở khóa cuộn trang cho body (Đề phòng quảng cáo block không cho cuộn khi in) */
                    body {
                        overflow: visible !important;
                        position: relative !important;
                        background-color: #fff !important;
                    }
                    
                    .cmeTable {
                        width: 100% !important;
                    }
                """
                )

                # Chuyển chế độ hiển thị sang dạng bản in (Print Media)
                await page.emulate_media(media="print")

                file_name = f"CME_{name}_Settlements_{date_str}.pdf"

                # Xuất định dạng PDF khổ Ngang chuẩn Audit
                await page.pdf(
                    path=file_name,
                    format="A4",
                    print_background=True,
                    display_header_footer=True,
                    scale=0.85,
                    landscape=True,
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
