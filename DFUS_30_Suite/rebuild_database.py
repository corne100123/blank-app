import os
from config import _get_configured_db_path_for_scripts, get_default_db_path
from db_helpers import initialize_schema, register_tenant


def rebuild_clients(db_path=None, biz_name=None, ncr_registration_number=None):
    if db_path is None:
        db_path = _get_configured_db_path_for_scripts()
    if not db_path:
        db_path = get_default_db_path()
    db_path = str(db_path)
    print(f"🔧 Connecting to {db_path}...")

    initialize_schema(db_path)

    if biz_name and ncr_registration_number:
        try:
            tenant_id = register_tenant(db_path, biz_name, ncr_registration_number)
            print(f"✅ Registered tenant '{biz_name}' with tenant_id={tenant_id}")
        except Exception as e:
            print(f"Unable to create tenant during rebuild: {e}")

    print("\n🎉 REBUILD COMPLETE!")
    print("👉 Restart Streamlit and continue with registration or login.")


if __name__ == "__main__":
    rebuild_clients()
