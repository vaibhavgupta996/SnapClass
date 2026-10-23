
import streamlit as st
import importlib.util
import sys

# --------------------------------------------------
# TEMPORARY DEBUG: Check Python and OpenCV
# --------------------------------------------------
st.write("Python version:", sys.version)
st.write("Python executable:", sys.executable)

try:
    cv2_spec = importlib.util.find_spec("cv2")
    st.write("OpenCV module found:", cv2_spec is not None)

    if cv2_spec is not None:
        import cv2
        st.write("OpenCV version:", cv2.__version__)
    else:
        st.error("OpenCV (cv2) is not available in this environment.")

except Exception as e:
    st.error("OpenCV import error:")
    st.code(f"{type(e).__name__}: {e}")

# --------------------------------------------------
# App imports
# --------------------------------------------------
from src.screens.home_screen import home_screen
from src.screens.student_screen import student_screen
from src.screens.teacher_screen import teacher_screen
from src.components.dialog_auto_enroll import auto_enroll_dialog


def main():
    st.set_page_config(
        page_title="SnapClass-Snap Your Attendance",
        page_icon="https://i.ibb.co/YTYGn5qV/logo.png"
    )

    if "login_type" not in st.session_state:
        st.session_state["login_type"] = None

    match st.session_state["login_type"]:
        case "teacher":
            teacher_screen()

        case "student":
            student_screen()

        case None:
            home_screen()

    join_code = st.query_params.get("join-code")

    if join_code:
        if st.session_state.login_type != "student":
            st.session_state.login_type = "student"
            st.rerun()

        if (
            st.session_state.get("is_logged_in")
            and st.session_state.get("user_role") == "student"
        ):
            auto_enroll_dialog(join_code)


if __name__ == "__main__":
    main()
