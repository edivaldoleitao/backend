from django.db import migrations

def inserir_dados(apps, schema_editor):
    MyModel = apps.get_model('api', 'Store')
    
    MyModel.objects.create(name='Amazon', url_base = 'https://www.amazon.com.br/')
    MyModel.objects.create(name='Kabum', url_base = 'https://www.kabum.com.br/')
    MyModel.objects.create(name='Terabyte', url_base = 'https://www.terabyteshop.com.br/')

class Migration(migrations.Migration):
    dependencies = [
        ('api', '0006_motherboard_delete_userhistory'),
    ]

    operations = [
        migrations.RunPython(inserir_dados),
    ]