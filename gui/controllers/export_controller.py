from core.services.export_service import ExportService

from core.services.setting_service import SettingsService


class ExportController:

    def __init__(self):

        self.settings = SettingsService()
        
        self.service = ExportService(self.settings)

    def fn_prepare_export(self):

        folder = self.service.fn_get_report_folder()

        print(f"[Export] Folder : {folder}")

        return folder