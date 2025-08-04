from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Buscar usuário admin
    admin_user = User.query.filter_by(email='admin@iaon.com').first()
    
    if admin_user:
        # Definir senha correta
        admin_user.password_hash = generate_password_hash('admin123')
        db.session.commit()
        print("✅ Senha do usuário admin corrigida!")
    else:
        print("❌ Usuário admin não encontrado")
    
    # Verificar outros usuários sem senha
    users_without_password = User.query.filter_by(password_hash=None).all()
    
    for user in users_without_password:
        # Definir senha padrão baseada no email
        default_password = user.email.split('@')[0] + '123'
        user.password_hash = generate_password_hash(default_password)
        print(f"✅ Senha definida para {user.email}: {default_password}")
    
    db.session.commit()
    print("🎉 Todas as senhas corrigidas!")
