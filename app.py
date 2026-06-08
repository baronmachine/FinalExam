import flet as ft
import httpx
import threading
import time

PRIMARY   = "#00695C"
ACCENT    = "#00897B"
PINK_BTN  = "#C62828"
SUCCESS   = "#00695C"
ROW_ODD   = "#D7EDE7"
ROW_EVEN  = "#FFFFFF"
HEADER_BG = "#333344"
TEXT_DK   = "#212121"
TEXT_SEC  = "#557570"
API_LABEL = "#00695C"
TF_BG     = "#CCE5EA"
PAGE_BG   = "#D7EDE7"

BASE_URL  = "http://127.0.0.1:8000"

COL_STYLE = ft.TextStyle(color="white", weight=ft.FontWeight.BOLD, size=13)


def make_tf(label):
    return ft.TextField(
        label=label,
        expand=True,
        bgcolor=TF_BG,
        filled=True,
        border_color=ACCENT,
        focused_border_color=PRIMARY,
        text_size=13,
        color=TEXT_DK,
        cursor_color=PRIMARY,
        label_style=ft.TextStyle(color="#557570"),
    )


def api_get():
    try:
        r = httpx.get(f"{BASE_URL}/doctors", timeout=5)
        r.raise_for_status()
        return r.json(), None
    except httpx.ConnectError:
        return None, "Server bağlantısı yoxdur. api.py-ni işlət."
    except Exception as ex:
        return None, str(ex)


def api_post(payload: dict):
    try:
        r = httpx.post(f"{BASE_URL}/doctors", json=payload, timeout=5)
        if r.status_code in (400, 422):
            try:
                return None, r.json().get("detail", "Xəta")
            except Exception:
                return None, "Validasiya xətası"
        r.raise_for_status()
        return r.json(), None
    except httpx.ConnectError:
        return None, "Server bağlantısı yoxdur."
    except Exception as ex:
        return None, str(ex)


def api_delete(doctor_id: int):
    try:
        r = httpx.delete(f"{BASE_URL}/doctors/{doctor_id}", timeout=5)
        if r.status_code == 404:
            return None, r.json().get("detail", "Tapılmadı")
        r.raise_for_status()
        return r.json(), None
    except httpx.ConnectError:
        return None, "Server bağlantısı yoxdur."
    except Exception as ex:
        return None, str(ex)


def window2(page: ft.Page, go_back):

    tf_id    = make_tf("DoctorID")
    tf_name  = make_tf("FullName")
    tf_spec  = make_tf("Specialization")
    tf_fee   = make_tf("Fee")

    banner = ft.Container(
        visible=False,
        border_radius=8,
        padding=ft.Padding.symmetric(vertical=12, horizontal=16),
        content=ft.Row(spacing=8, controls=[
            ft.Icon(ft.Icons.CHECK_CIRCLE, color="white", size=18),
            ft.Text("", color="white", weight=ft.FontWeight.BOLD, size=13),
        ]),
    )

    table_col = ft.Ref[ft.Column]()

    def build_table(rows):
        return ft.DataTable(
            expand=True,
            width=float("inf"),
            bgcolor=ft.Colors.TRANSPARENT,
            border=ft.Border.all(0),
            heading_row_color=HEADER_BG,
            heading_row_height=40,
            data_row_min_height=36,
            data_row_max_height=48,
            column_spacing=16,
            columns=[
                ft.DataColumn(ft.Text("DoctorID",       style=COL_STYLE)),
                ft.DataColumn(ft.Text("FullName",      style=COL_STYLE)),
                ft.DataColumn(ft.Text("Specialization",style=COL_STYLE)),
                ft.DataColumn(ft.Text("Fee",           style=COL_STYLE)),
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(r["id"]),            color=TEXT_DK, size=13)),
                        ft.DataCell(ft.Text(r["name"],               color=TEXT_DK, size=13)),
                        ft.DataCell(ft.Text(r["specialization"],     color=TEXT_DK, size=13)),
                        ft.DataCell(ft.Text(f"{r['fee']:.2f}",       color=TEXT_DK, size=13)),
                    ],
                    color=ROW_ODD if i % 2 == 0 else ROW_EVEN,
                )
                for i, r in enumerate(rows)
            ],
        )

    def refresh_table():
        data, err = api_get()
        if err:
            show_banner(err, is_error=True)
            return
        table_col.current.controls = [build_table(data)]
        page.update()

    def clear_form():
        for f in [tf_id, tf_name, tf_spec, tf_fee]:
            f.value = ""
            f.error_text = None

    def show_banner(msg: str, is_error=False):
        banner.bgcolor = "#C62828" if is_error else SUCCESS
        banner.content.controls[0].name = ft.Icons.ERROR if is_error else ft.Icons.CHECK_CIRCLE
        banner.content.controls[1].value = msg
        banner.visible = True
        page.update()
        def hide():
            time.sleep(3)
            banner.visible = False
            page.update()
        threading.Thread(target=hide, daemon=True).start()

    def post_add(e):
        for f in [tf_id, tf_name, tf_spec, tf_fee]:
            f.error_text = None
        missing = False
        for f, lbl in [(tf_id,"ID"),(tf_name,"Name"),(tf_spec,"Specialization"),(tf_fee,"Fee")]:
            if not f.value:
                f.error_text = "Tələb olunur"
                missing = True
        if missing:
            page.update()
            return
        try:
            new_id  = int(tf_id.value)
            new_fee = float(tf_fee.value)
        except ValueError:
            if not tf_id.value.isdigit():
                tf_id.error_text = "Rəqəm olmalıdır"
            try:
                float(tf_fee.value)
            except ValueError:
                tf_fee.error_text = "Float olmalıdır"
            page.update()
            return

        payload = {
            "DoctorID":       new_id,
            "FullName":       tf_name.value,
            "Specialization": tf_spec.value,
            "Fee":            new_fee,
        }
        result, err = api_post(payload)
        if err:
            show_banner(str(err), is_error=True)
            return
        clear_form()
        refresh_table()
        show_banner("Record added successfully!")

    def do_delete(e):
        tf_id.error_text = None
        if not tf_id.value:
            tf_id.error_text = "ID daxil et"
            page.update()
            return
        try:
            del_id = int(tf_id.value)
        except ValueError:
            tf_id.error_text = "Rəqəm olmalıdır"
            page.update()
            return
        result, err = api_delete(del_id)
        if err:
            show_banner(str(err), is_error=True)
            return
        clear_form()
        refresh_table()
        show_banner("Record deleted successfully!")

    init_data, _ = api_get()
    init_rows = init_data if init_data else []

    content = ft.Column(
        expand=True,
        spacing=0,
        controls=[
            ft.Container(
                bgcolor=PRIMARY,
                padding=ft.Padding.symmetric(horizontal=8, vertical=10),
                content=ft.Row([
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color="white",
                                  on_click=lambda _: go_back()),
                    ft.Text("Add Doctor", color="white", size=18,
                            weight=ft.FontWeight.BOLD, expand=True,
                            text_align=ft.TextAlign.CENTER),
                    ft.Container(width=48),
                ]),
            ),

            ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=0,
                controls=[
                    ft.Container(
                        padding=ft.Padding.all(14),
                        content=ft.Column(spacing=10, controls=[

                            ft.Text("Table: Doctors — GET /doctors",
                                    color=API_LABEL, weight=ft.FontWeight.BOLD, size=13),
                            ft.ProgressBar(value=1, color=PRIMARY, bgcolor="#B2DFDB"),

                            ft.Container(
                                border=ft.Border.all(1, "#B2DFDB"),
                                border_radius=8,
                                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                                content=ft.Row(expand=True, controls=[
                                    ft.Column(
                                        ref=table_col,
                                        expand=True,
                                        controls=[build_table(init_rows)],
                                    ),
                                ]),
                            ),

                            ft.Divider(height=6, color=ft.Colors.TRANSPARENT),

                            ft.Text("Add New Record — POST /doctors",
                                    color=API_LABEL, weight=ft.FontWeight.BOLD, size=13),

                            ft.Row([tf_id,   tf_name], spacing=10),
                            ft.Row([tf_spec, tf_fee],  spacing=10),

                            ft.Divider(height=4, color=ft.Colors.TRANSPARENT),

                            ft.Row(spacing=10, controls=[
                                ft.ElevatedButton(
                                    "POST Add", expand=True,
                                    bgcolor=PRIMARY, color="white", height=46,
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                                    on_click=post_add,
                                ),
                                ft.ElevatedButton(
                                    "DELETE", expand=True,
                                    bgcolor=PINK_BTN, color="white", height=46,
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                                    on_click=do_delete,
                                ),
                            ]),

                            banner,
                        ]),
                    ),
                ],
            ),
        ],
    )

    return content


def window1(page: ft.Page, go_to_add):

    bs_title    = ft.Text("", color=PRIMARY, weight=ft.FontWeight.BOLD, size=14)
    bs_subtitle = ft.Text("", color=TEXT_DK, size=13)
    bs_hint     = ft.Text("Tap drag handle to expand",
                          color=TEXT_SEC, italic=True, size=11)

    bottom_sheet = ft.BottomSheet(
        dismissible=True,
        show_drag_handle=True,
        bgcolor="white",
        content=ft.Container(
            padding=ft.Padding(left=20, top=8, right=20, bottom=24),
            content=ft.Column(tight=True, controls=[
                ft.Container(height=4),
                bs_title,
                ft.Container(height=4),
                bs_subtitle,
                ft.Container(height=6),
                bs_hint,
            ]),
        ),
        on_dismiss=lambda e: None,
    )

    def open_bs(row_data: dict):
        bs_title.value    = "DOCTOR DETAILS"
        bs_subtitle.value = (f"{row_data['name']} · {row_data['specialization']} · "
                             f"Fee: {row_data['fee']:.2f}")
        page.show_dialog(bottom_sheet)

    def build_clickable_table(rows):
        data_rows = []
        for i, r in enumerate(rows):
            rd = r
            data_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(rd["id"]),          color=TEXT_DK, size=13)),
                        ft.DataCell(ft.Text(rd["name"],             color=TEXT_DK, size=13)),
                        ft.DataCell(ft.Text(rd["specialization"],   color=TEXT_DK, size=13)),
                        ft.DataCell(ft.Text(f"{rd['fee']:.2f}",     color=TEXT_DK, size=13)),
                    ],
                    color=ROW_ODD if i % 2 == 0 else ROW_EVEN,
                    on_select_change=lambda e, d=rd: open_bs(d),
                )
            )
        return ft.DataTable(
            expand=True,
            width=float("inf"),
            bgcolor=ft.Colors.TRANSPARENT,
            border=ft.Border.all(0),
            heading_row_color=HEADER_BG,
            heading_row_height=40,
            data_row_min_height=36,
            data_row_max_height=48,
            column_spacing=16,
            columns=[
                ft.DataColumn(ft.Text("DoctorID",       style=COL_STYLE)),
                ft.DataColumn(ft.Text("FullName",       style=COL_STYLE)),
                ft.DataColumn(ft.Text("Specialization", style=COL_STYLE)),
                ft.DataColumn(ft.Text("Fee",            style=COL_STYLE)),
            ],
            rows=data_rows,
        )

    table_col = ft.Ref[ft.Column]()
    body      = ft.Ref[ft.Container]()
    err_text  = ft.Ref[ft.Text]()
    avg_text  = ft.Ref[ft.Text]()

    def compute_avg(rows):
        if not rows:
            return 0.0
        return sum(r["fee"] for r in rows) / len(rows)

    def refresh_main_table():
        data, err = api_get()
        if err:
            if err_text.current:
                err_text.current.value = err
                err_text.current.visible = True
        else:
            if err_text.current:
                err_text.current.visible = False
            if table_col.current:
                table_col.current.controls = [build_clickable_table(data)]
            if avg_text.current:
                avg_text.current.value = f"Average Consultation Fee: {compute_avg(data):.2f}"
        page.update()

    def doctors_view():
        init_data, init_err = api_get()
        init_rows = init_data if init_data else []
        init_avg  = compute_avg(init_rows)

        return ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=8,
            controls=[
                ft.Container(
                    bgcolor="#B2DFDB", border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                    content=ft.Text("GET /doctors  →  loads data on open",
                                    color=PRIMARY, size=11),
                ),
                ft.ProgressBar(value=1, color=PRIMARY, bgcolor="#B2DFDB"),

                ft.Text(
                    ref=err_text,
                    value=init_err or "",
                    color="#C62828", size=12,
                    visible=bool(init_err),
                ),

                ft.Container(
                    border=ft.Border.all(1, "#B2DFDB"),
                    border_radius=8,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    content=ft.Row(expand=True, controls=[
                        ft.Column(
                            ref=table_col,
                            expand=True,
                            controls=[build_clickable_table(init_rows)],
                        ),
                    ]),
                ),

                ft.Container(
                    bgcolor="white",
                    border=ft.Border.all(1, PRIMARY),
                    border_radius=8,
                    padding=ft.Padding.symmetric(horizontal=14, vertical=12),
                    content=ft.Text(
                        ref=avg_text,
                        value=f"Average Consultation Fee: {init_avg:.2f}",
                        color=PRIMARY,
                        weight=ft.FontWeight.BOLD,
                        size=14,
                    ),
                ),
            ],
        )

    def appointments_view():
        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            controls=[
                ft.Container(height=40),
                ft.Icon(ft.Icons.CALENDAR_MONTH, size=56, color=ACCENT),
                ft.Text("Appointments", size=18, color=TEXT_SEC),
                ft.Text("Görüşlər siyahısı burada olacaq.",
                        color=TEXT_SEC, size=13, text_align=ft.TextAlign.CENTER),
            ],
        )

    def profile_view():
        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            controls=[
                ft.Container(height=40),
                ft.Icon(ft.Icons.PERSON, size=56, color=ACCENT),
                ft.Text("Profile", size=18, color=TEXT_SEC),
                ft.Text("İstifadəçi profili burada olacaq.",
                        color=TEXT_SEC, size=13, text_align=ft.TextAlign.CENTER),
            ],
        )

    views = [doctors_view, appointments_view, profile_view]

    def on_nav_change(e):
        idx = e.control.selected_index
        body.current.content = views[idx]()
        if idx == 0:
            refresh_main_table()
        else:
            page.update()

    content = ft.Column(
        expand=True,
        spacing=0,
        controls=[
            ft.Container(
                bgcolor=PRIMARY,
                padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                content=ft.Row([
                    ft.Text("HospitalApp", color="white", size=18,
                            weight=ft.FontWeight.BOLD, expand=True),
                    ft.IconButton(icon=ft.Icons.MENU, icon_color="white",
                                  on_click=lambda _: go_to_add(),
                                  tooltip="Add Doctor"),
                ]),
            ),

            ft.Container(
                ref=body,
                expand=True,
                padding=ft.Padding.all(14),
                content=doctors_view(),
            ),

            ft.NavigationBar(
                selected_index=0,
                bgcolor="white",
                indicator_color="#B2DFDB",
                on_change=on_nav_change,
                destinations=[
                    ft.NavigationBarDestination(icon=ft.Icons.LOCAL_HOSPITAL, label="Doctors"),
                    ft.NavigationBarDestination(icon=ft.Icons.CALENDAR_MONTH, label="Appointments"),
                    ft.NavigationBarDestination(icon=ft.Icons.PERSON,         label="Profile"),
                ],
            ),
        ],
    )

    return content, refresh_main_table


def main(page: ft.Page):
    page.title    = "HospitalApp"
    page.bgcolor  = PAGE_BG
    page.padding  = 0
    page.window.width     = 420
    page.window.height    = 780
    page.window.resizable = True

    root = ft.Ref[ft.Stack]()

    def go_to_add():
        root.current.controls[1].visible = True
        root.current.controls[0].visible = False
        page.update()

    def go_back():
        root.current.controls[0].visible = True
        root.current.controls[1].visible = False
        refresh_w1()
        page.update()

    w1, refresh_w1 = window1(page, go_to_add)
    w2 = window2(page, go_back)

    page.add(
        ft.Stack(
            ref=root,
            expand=True,
            controls=[
                ft.Container(content=w1, expand=True, visible=True),
                ft.Container(content=w2, expand=True, visible=False),
            ],
        )
    )


ft.run(main)
