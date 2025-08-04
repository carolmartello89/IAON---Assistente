from app import app, db, User

with app.app_context():
    users = User.query.all()
    print("Usuários disponíveis:")
    for user in users:
        print(f'- Email: {user.email}')
        print(f'  Nome: {user.full_name}')
        print(f'  Ativo: {user.is_active}')
        print(f'  Admin: {getattr(user, "is_admin", False)}')
        print()
