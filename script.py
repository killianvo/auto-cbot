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
        # Giữ nguyên cấu hình bypass Cloudflare hoạt động tốt của bạn
        browser = await p.chromium.launch(
            headless=False, args=["--headless=new"]
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
                # Đợi 12 giây cho bảng dữ liệu cốt lõi tải xong
                await page.wait_for_timeout(12000)

                # Cuộn chuột xuống đáy và lên đỉnh để ép load hết các tháng kỳ hạn xa
                await page.evaluate(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                await page.wait_for_timeout(3000)
                await page.evaluate("window.scrollTo(0, 0);")
                await page.wait_for_timeout(1000)

                # KỸ THUẬT QUAN TRỌNG: Tiêm bộ lọc CSS chặn đứng mọi loại bảng quảng cáo xuất hiện muộn
                # Nhắm mục tiêu chính xác vào các khung quảng cáo góc trái/phải, hộp thoại khảo sát, phản hồi (feedback)
                await page.add_style_tag(
                    content="""
                    /* 1. Ẩn menu chính, banner cookie và chân trang */
                    header.cmeHeader, .cmeFooter, #onetrust-banner-sdk, #onetrust-consent-sdk, .cookie-consent, .modal-backdrop, .parbase.banner { 
                        display: none !important; 
                    }
                    
                    /* 2. TIÊU DIỆT TẬN GỐC BẢNG QUẢNG CÁO/KHẢO SÁT/FEEDBACK GÓC DƯỚI BÊN TRÁI VÀ PHẢI (Sửa lỗi cho Wheat) */
                    [id*="onetrust"], [class*="onetrust"], [class*="privacy"], [id*="privacy"],
                    [class*="feedback"], [id*="feedback"], [class*="survey"], [id*="survey"],
                    [class*="popup"], [id*="popup"], [class*="modal"], [id*="modal"],
                    .truste-cookie-banner, #tealium-consent, .invitation, #invitation,
                    [class*="ad-slot"], [class*="advertisement"], [id*="google_ads"],
                    iframe[src*="doubleclick"], iframe[src*="googleads"], div[id*="survey"] {
                        display: none !important;
                        visibility: hidden !important;
                        opacity: 0 !important;
                        height: 0 !important;
                        width: 0 !important;
                        pointer-events: none !important;
                    }

                    /* 3. Ép bẻ gãy khung cuộn để hiển thị đủ tất cả các tháng tương lai (Future months) */
                    .cmeTable-wrapper, .table-responsive, .main-content, html, body {
                        overflow: visible !important;
                        max-height: none !important;
                        height: auto !important;
                    }
                """
                )

                # Thực thi bổ sung bấm nút tắt Cookie bằng Javascript nếu nó xuất hiện sớm
                await page.evaluate("""() => {
                    const cookieBtn = document.querySelector('#onetrust-accept-btn-handler');
                    if (cookieBtn) cookieBtn.click();
                }""")

                # Chờ thêm 2 giây để toàn bộ bố cục trang phẳng lặng hoàn toàn trước khi bấm in
                await page.wait_for_timeout(2000)

                # Chuyển sang định dạng media bản in
                await page.emulate_media(media="print")

                file_name = f"CME_{name}_Settlements_{date_str}.pdf"

                # Xuất bản in khổ ngang sắc nét chuẩn kiểm toán
                await page.pdf(
                    path=file_name,
                    format="A4",
                    print_background=True,
                    display_header_footer=True,
                    scale=0.85,
                    landscape=True,
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
