from django.apps import AppConfig


class PanelproductividadConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'panelproductividad'
    
    def ready(self):
        import panelproductividad.signals
