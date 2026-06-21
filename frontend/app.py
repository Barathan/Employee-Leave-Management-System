"""
Employee Leave Management System - Streamlit frontend.

Run the FastAPI backend first (see README), then:
    streamlit run frontend/app.py
"""
from datetime import date, datetime

import pandas as pd
import plotly.express as px
import streamlit as st

import api_client as api

# ----------------------------------------------------------------------------
# Page configuration & global styling
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Employee Leave Management",
    page_icon="🗓️",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .block-container {padding-top: 2rem; padding-bottom: 3rem;}

    .app-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2c5f7c 100%);
        padding: 1.6rem 2rem;
        border-radius: 14px;
        margin-bottom: 1.6rem;
        color: white;
    }
    .app-header h1 {margin: 0; font-size: 1.6rem;}
    .app-header p {margin: 0.2rem 0 0 0; opacity: 0.85; font-size: 0.95rem;}

    .metric-card {
        background: #ffffff;
        border: 1px solid #e6e9ef;
        border-radius: 12px;
        padding: 1.1rem 1.3rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e6e9ef;
        border-radius: 12px;
        padding: 0.9rem 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    .status-pending {color: #b8860b; font-weight: 600;}
    .status-approved {color: #1a7f37; font-weight: 600;}
    .status-rejected {color: #c92a2a; font-weight: 600;}

    section[data-testid="stSidebar"] {
        background-color: #16243a;
    }
    section[data-testid="stSidebar"] * {color: #f0f2f6 !important;}
    section[data-testid="stSidebar"] .stRadio > label {color: #f0f2f6 !important;}

    /* Sidebar buttons (e.g. Logout) need their own background/text so they
       don't inherit invisible white-on-white from the rule above. */
    section[data-testid="stSidebar"] .stButton>button {
        background-color: #c92a2a !important;
        color: #ffffff !important;
        border: 1px solid #a82323 !important;
    }
    section[data-testid="stSidebar"] .stButton>button:hover {
        background-color: #a82323 !important;
        border: 1px solid #8c1d1d !important;
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] .stButton>button p {
        color: #ffffff !important;
    }

    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------------
def init_state():
    defaults = {
        "token": None,
        "role": None,
        "user_id": None,
        "full_name": None,
        "username": None,
        "page": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


def logout():
    for k in ["token", "role", "user_id", "full_name", "username", "page"]:
        st.session_state[k] = None
    st.rerun()


def handle_response(resp, success_msg=None):
    """Common error surface for API responses. Returns parsed JSON or None."""
    if resp is None:
        st.error("Could not reach the backend API. Is it running?")
        return None
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        st.error(f"Error: {detail}")
        return None
    if success_msg:
        st.success(success_msg)
    return resp.json()


def status_badge(status: str) -> str:
    css_class = {
        "Pending": "status-pending",
        "Approved": "status-approved",
        "Rejected": "status-rejected",
    }.get(status, "")
    return f'<span class="{css_class}">{status}</span>'


# ----------------------------------------------------------------------------
# Login page
# ----------------------------------------------------------------------------
def login_page():
    st.markdown(
        """
        <div class="app-header">
            <h1>🗓️ Employee Leave Management System</h1>
            <p>Sign in to manage leave applications and approvals</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.container(border=True):
            st.subheader("Sign In")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_clicked = st.button("Login", use_container_width=True, type="primary")

            if login_clicked:
                if not username or not password:
                    st.warning("Please enter both username and password.")
                else:
                    try:
                        with st.spinner("Signing in..."):
                            resp = api.login(username, password)
                    except Exception as e:
                        st.error(f"Could not reach the backend API at {api.BASE_URL}. "
                                 f"Make sure it's running. ({e})")
                        resp = None

                    data = handle_response(resp)
                    if data:
                        st.session_state.token = data["access_token"]
                        st.session_state.role = data["role"]
                        st.session_state.user_id = data["user_id"]
                        st.session_state.full_name = data["full_name"]
                        st.session_state.username = username
                        st.rerun()

            st.caption("First time? Default manager login -> **admin / admin123** "
                       "(created by running `seed_data.py`).")


# ----------------------------------------------------------------------------
# Shared widgets
# ----------------------------------------------------------------------------
def render_leave_table(leaves: list, show_employee: bool = False):
    if not leaves:
        st.info("No leave records found.")
        return
    df = pd.DataFrame(leaves)
    cols = ["id", "leave_type", "start_date", "end_date", "days", "reason", "status"]
    if show_employee:
        cols.insert(1, "employee_name")
    df = df[[c for c in cols if c in df.columns]]
    df = df.rename(columns={
        "id": "ID", "employee_name": "Employee", "leave_type": "Type",
        "start_date": "From", "end_date": "To", "days": "Days",
        "reason": "Reason", "status": "Status",
    })
    st.dataframe(df, use_container_width=True, hide_index=True)


# ----------------------------------------------------------------------------
# MANAGER PAGES
# ----------------------------------------------------------------------------
def manager_employee_dashboard():
    st.subheader("🧑‍💼 Employee Dashboard")
    with st.spinner("Loading employee directory..."):
        resp = api.list_employees()
    employees = handle_response(resp) or []

    if not employees:
        st.info("No employees registered yet.")
        return

    df = pd.DataFrame(employees)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Employees", len(df[df["role"] == "employee"]))
    c2.metric("Managers", len(df[df["role"] == "manager"]))
    c3.metric("Departments", df["department"].nunique())
    c4.metric("Active Accounts", int(df["is_active"].sum()))

    st.markdown("#### Directory")
    dept_filter = st.selectbox("Filter by department", ["All"] + sorted(df["department"].unique().tolist()))
    view = df if dept_filter == "All" else df[df["department"] == dept_filter]

    display_df = view[[
        "id", "full_name", "username", "email", "role", "department",
        "designation", "annual_leave_balance", "sick_leave_balance", "casual_leave_balance"
    ]].rename(columns={
        "id": "ID", "full_name": "Name", "username": "Username", "email": "Email",
        "role": "Role", "department": "Department", "designation": "Designation",
        "annual_leave_balance": "Annual Bal.", "sick_leave_balance": "Sick Bal.",
        "casual_leave_balance": "Casual Bal.",
    })
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def manager_approval_dashboard():
    st.subheader("✅ Leave Approval Dashboard")

    tab_pending, tab_all = st.tabs(["Pending Requests", "All Requests"])

    with tab_pending:
        with st.spinner("Loading pending requests..."):
            resp = api.pending_leaves()
        pending = handle_response(resp) or []

        if not pending:
            st.success("No pending leave requests. You're all caught up!")
        else:
            for leave in pending:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"**{leave['employee_name']}** — {leave['leave_type']} Leave")
                        st.write(f"📅 {leave['start_date']} → {leave['end_date']}  "
                                 f"({leave['days']} day(s))")
                        st.write(f"📝 {leave['reason']}")
                        st.caption(f"Applied on {leave['applied_on'][:16].replace('T', ' ')}")
                    with c2:
                        comment = st.text_input(
                            "Comment", key=f"comment_{leave['id']}", placeholder="Optional"
                        )
                        bcol1, bcol2 = st.columns(2)
                        if bcol1.button("✅ Approve", key=f"approve_{leave['id']}", use_container_width=True):
                            with st.spinner("Approving..."):
                                r = api.review_leave(leave["id"], {"status": "Approved", "review_comment": comment})
                            if handle_response(r, "Leave approved."):
                                st.rerun()
                        if bcol2.button("❌ Reject", key=f"reject_{leave['id']}", use_container_width=True):
                            with st.spinner("Rejecting..."):
                                r = api.review_leave(leave["id"], {"status": "Rejected", "review_comment": comment})
                            if handle_response(r, "Leave rejected."):
                                st.rerun()

    with tab_all:
        status_filter = st.selectbox("Filter by status", ["All", "Pending", "Approved", "Rejected"])
        with st.spinner("Loading leave requests..."):
            resp = api.all_leaves(status=None if status_filter == "All" else status_filter)
        leaves = handle_response(resp) or []
        render_leave_table(leaves, show_employee=True)


def manager_register_employee():
    st.subheader("➕ Register Employee")

    with st.form("register_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            full_name = st.text_input("Full Name *")
            username = st.text_input("Username *")
            email = st.text_input("Email *")
            password = st.text_input("Temporary Password *", type="password")
        with c2:
            role = st.selectbox("Role", ["employee", "manager"])
            department = st.text_input("Department", value="General")
            designation = st.text_input("Designation", value="Staff")
            phone = st.text_input("Phone", value="")

        st.markdown("##### Initial Leave Balances (days)")
        b1, b2, b3 = st.columns(3)
        annual = b1.number_input("Annual", min_value=0.0, value=18.0, step=1.0)
        sick = b2.number_input("Sick", min_value=0.0, value=10.0, step=1.0)
        casual = b3.number_input("Casual", min_value=0.0, value=7.0, step=1.0)

        submitted = st.form_submit_button("Register Employee", type="primary", use_container_width=True)

        if submitted:
            if not all([full_name, username, email, password]):
                st.warning("Please fill in all required fields (marked *).")
            else:
                payload = {
                    "full_name": full_name,
                    "username": username,
                    "email": email,
                    "password": password,
                    "role": role,
                    "department": department,
                    "designation": designation,
                    "phone": phone,
                    "annual_leave_balance": annual,
                    "sick_leave_balance": sick,
                    "casual_leave_balance": casual,
                }
                with st.spinner("Registering employee..."):
                    resp = api.register_employee(payload)
                data = handle_response(resp, f"{full_name} registered successfully as {role}.")
                if data:
                    st.balloons()


def manager_leave_statistics():
    st.subheader("📊 Leave Statistics")

    with st.spinner("Crunching leave statistics..."):
        resp = api.statistics()
    stats = handle_response(resp)
    if not stats:
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Requests", stats["total"])
    c2.metric("Pending", stats["pending"])
    c3.metric("Approved", stats["approved"])
    c4.metric("Rejected", stats["rejected"])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Requests by Leave Type")
        if stats["by_type"]:
            type_df = pd.DataFrame(
                {"Leave Type": list(stats["by_type"].keys()), "Count": list(stats["by_type"].values())}
            )
            fig = px.pie(type_df, names="Leave Type", values="Count", hole=0.45,
                         color_discrete_sequence=px.colors.sequential.Blues_r)
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No leave data yet.")

    with col2:
        st.markdown("#### Requests by Department")
        if stats["by_department"]:
            dept_df = pd.DataFrame(
                {"Department": list(stats["by_department"].keys()), "Count": list(stats["by_department"].values())}
            )
            fig2 = px.bar(dept_df, x="Department", y="Count", color="Department",
                          color_discrete_sequence=px.colors.sequential.Teal)
            fig2.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No leave data yet.")

    st.markdown("#### Approval Status Breakdown")
    status_df = pd.DataFrame({
        "Status": ["Pending", "Approved", "Rejected"],
        "Count": [stats["pending"], stats["approved"], stats["rejected"]],
    })
    fig3 = px.bar(status_df, x="Status", y="Count", color="Status",
                  color_discrete_map={"Pending": "#d4a017", "Approved": "#1a7f37", "Rejected": "#c92a2a"})
    fig3.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)


# ----------------------------------------------------------------------------
# EMPLOYEE PAGES
# ----------------------------------------------------------------------------
def employee_apply_leave():
    st.subheader("📝 Apply for Leave")

    with st.spinner("Loading your leave balances..."):
        me = handle_response(api.get_me())
    if not me:
        return

    b1, b2, b3 = st.columns(3)
    b1.metric("Annual Balance", f"{me['annual_leave_balance']} days")
    b2.metric("Sick Balance", f"{me['sick_leave_balance']} days")
    b3.metric("Casual Balance", f"{me['casual_leave_balance']} days")

    st.divider()

    with st.form("apply_leave_form", clear_on_submit=True):
        leave_type = st.selectbox("Leave Type", ["Annual", "Sick", "Casual", "Unpaid"])
        c1, c2 = st.columns(2)
        start_date = c1.date_input("Start Date", value=date.today(), min_value=date.today())
        end_date = c2.date_input("End Date", value=date.today(), min_value=date.today())
        reason = st.text_area("Reason for Leave *", placeholder="Briefly describe the reason...")

        submitted = st.form_submit_button("Submit Application", type="primary", use_container_width=True)

        if submitted:
            if not reason or len(reason.strip()) < 3:
                st.warning("Please provide a reason (at least 3 characters).")
            elif end_date < start_date:
                st.warning("End date cannot be before start date.")
            else:
                payload = {
                    "leave_type": leave_type,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "reason": reason,
                }
                with st.spinner("Submitting application..."):
                    resp = api.apply_leave(payload)
                data = handle_response(resp, "Leave application submitted successfully!")
                if data:
                    st.rerun()


def employee_leave_history():
    st.subheader("📜 My Leave History")

    with st.spinner("Loading your leave history..."):
        resp = api.my_leaves()
    leaves = handle_response(resp) or []

    if not leaves:
        st.info("You haven't applied for any leave yet.")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Applications", len(leaves))
    c2.metric("Approved", sum(1 for l in leaves if l["status"] == "Approved"))
    c3.metric("Pending", sum(1 for l in leaves if l["status"] == "Pending"))

    status_filter = st.selectbox("Filter by status", ["All", "Pending", "Approved", "Rejected"])
    filtered = leaves if status_filter == "All" else [l for l in leaves if l["status"] == status_filter]

    for leave in filtered:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{leave['leave_type']} Leave** — {leave['days']} day(s)")
                st.write(f"📅 {leave['start_date']} → {leave['end_date']}")
                st.write(f"📝 {leave['reason']}")
                if leave.get("review_comment"):
                    st.caption(f"Manager comment: {leave['review_comment']}")
            with c2:
                st.markdown(status_badge(leave["status"]), unsafe_allow_html=True)
                st.caption(f"Applied {leave['applied_on'][:10]}")


def employee_details_page():
    st.subheader("👤 My Details")

    with st.spinner("Loading your profile..."):
        me = handle_response(api.get_me())
    if not me:
        return

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(
            f"""
            <div class="metric-card" style="text-align:center;">
                <div style="font-size:3rem;">🧑</div>
                <h3 style="margin:0.3rem 0;">{me['full_name']}</h3>
                <p style="color:#666; margin:0;">{me['designation']}</p>
                <p style="color:#999; margin:0;">{me['department']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        with st.container(border=True):
            st.markdown("##### Profile Information")
            st.write(f"**Username:** {me['username']}")
            st.write(f"**Email:** {me['email']}")
            st.write(f"**Phone:** {me['phone'] or '—'}")
            st.write(f"**Role:** {me['role'].capitalize()}")
            st.write(f"**Joining Date:** {me['joining_date']}")
            st.write(f"**Status:** {'🟢 Active' if me['is_active'] else '🔴 Inactive'}")

    st.markdown("##### Leave Balances")
    b1, b2, b3 = st.columns(3)
    b1.metric("Annual Leave", f"{me['annual_leave_balance']} days")
    b2.metric("Sick Leave", f"{me['sick_leave_balance']} days")
    b3.metric("Casual Leave", f"{me['casual_leave_balance']} days")


# ----------------------------------------------------------------------------
# Main app shell
# ----------------------------------------------------------------------------
MANAGER_PAGES = {
    "🧑‍💼 Employee Dashboard": manager_employee_dashboard,
    "✅ Leave Approval Dashboard": manager_approval_dashboard,
    "➕ Register Employee": manager_register_employee,
    "📊 Leave Statistics": manager_leave_statistics,
}

EMPLOYEE_PAGES = {
    "📝 Apply Leave": employee_apply_leave,
    "📜 Leave History": employee_leave_history,
    "👤 My Details": employee_details_page,
}


def main_app():
    pages = MANAGER_PAGES if st.session_state.role == "manager" else EMPLOYEE_PAGES

    with st.sidebar:
        st.markdown(f"### 🗓️ Leave Manager")
        st.markdown(f"**{st.session_state.full_name}**")
        st.caption(f"Role: {st.session_state.role.capitalize()}")
        st.divider()

        choice = st.radio("Navigate", list(pages.keys()), label_visibility="collapsed")

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            logout()

    st.markdown(
        f"""
        <div class="app-header">
            <h1>🗓️ Employee Leave Management System</h1>
            <p>Welcome back, {st.session_state.full_name} ({st.session_state.role.capitalize()})</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    pages[choice]()


# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------
if st.session_state.token is None:
    login_page()
else:
    main_app()