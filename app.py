import streamlit as st


st.set_page_config(
    page_title="NFL Pick'em Intelligence Dashboard",
    page_icon="🏈",
    layout="wide",
)


if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False


def home_page():
    st.title("NFL Pick'em Intelligence Dashboard")

    st.write(
        "Weekly picks, player analytics, standings, "
        "and pool insights."
    )

    st.subheader("Dashboard")

    st.write(
        "Use the navigation menu to explore the app."
    )


with st.sidebar:

    if not st.session_state.admin_authenticated:

        with st.expander("Admin Login"):

            password = st.text_input(
                "Password",
                type="password",
            )

            if st.button(
                "Log In",
                key="admin_login",
            ):

                if password == st.secrets[
                    "admin_password"
                ]:
                    st.session_state[
                        "admin_authenticated"
                    ] = True

                    st.rerun()

                else:
                    st.error(
                        "Incorrect password."
                    )

    else:

        st.success(
            "Admin access enabled."
        )

        if st.button(
            "Log Out",
            key="admin_logout",
        ):
            st.session_state[
                "admin_authenticated"
            ] = False

            st.rerun()


pages = [
    st.Page(
        home_page,
        title="Home",
        icon="🏠",
        default=True,
    ),
    st.Page(
        "pages/1_Weekly_Picks.py",
        title="Weekly Picks",
        icon="🏈",
    ),
    st.Page(
        "pages/2_Player_Explorer.py",
        title="Player Explorer",
        icon="👤",
    ),
    st.Page(
        "pages/3_Standings.py",
        title="Standings",
        icon="🏆",
    ),
    st.Page(
        "pages/4_Pool_Insights.py",
        title="Pool Insights",
        icon="📊",
    ),
]


if st.session_state.admin_authenticated:

    pages.append(
        st.Page(
            "pages/5_Admin.py",
            title="Admin",
            icon="🔒",
        )
    )


page = st.navigation(
    pages
)

page.run()