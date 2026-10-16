"""Use cases for user management."""
from typing import Optional

from sqlalchemy.exc import IntegrityError

from app.infrastructure.database.repositories import UserRepository
from app.infrastructure.security.jwt_handler import (
    hash_password, verify_password, create_access_token, create_refresh_token
)
from app.domain.entities import User
from app.shared.exceptions import (
    ValidationException, AuthenticationException, DuplicateResourceException
)
from app.shared.constants.enums import UserRole


class RegisterUserUseCase:
    """Use case for user registration."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def execute(self, username: str, password: str, full_name: str, role: str = "CAMARERO", phone: Optional[str] = None) -> User:
        """Register a new user."""
        # Validate input
        if len(password) < 8:
            raise ValidationException("La contraseña debe tener al menos 8 caracteres")
        
        # Check if user already exists (including deleted users)
        existing_user = await self.user_repository.get_by_username(username, include_deleted=True)
        if existing_user:
            raise DuplicateResourceException(f"El usuario '{username}' ya existe")
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user
        user = User(
            username=username,
            email=f"{username}@no-email.local",
            password_hash=password_hash,
            full_name=full_name,
            role=role,
            is_active=True,
            phone=phone,
        )
        
        try:
            created_user = await self.user_repository.create(user)
            await self.user_repository.session.commit()
            return created_user
        except IntegrityError as exc:
            error_message = str(exc.orig).lower() if exc.orig else ""
            if "username" in error_message:
                raise DuplicateResourceException(f"El usuario '{username}' ya existe")
            if "email" in error_message:
                raise DuplicateResourceException(f"El email '{user.email}' ya está registrado")
            raise DuplicateResourceException("El usuario ya existe") from exc


class LoginUserUseCase:
    """Use case for user login."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def execute(self, username: str, password: str, role: Optional[str] = None) -> tuple[User, str, str]:
        """Login user and return tokens. El rol es opcional y no bloquea el login;
        cualquier usuario válido y activo puede iniciar sesión sin importar el rol
        enviado (necesario para recargas y sección Auxiliares)."""
        user = await self.user_repository.get_by_username(username)

        if not user:
            raise AuthenticationException("Usuario o contraseña inválidos")

        if not user.is_active:
            raise AuthenticationException(f'El usuario "{user.username}" está inactivo, no puede ingresar')
        
        if not verify_password(password, user.password_hash):
            raise AuthenticationException("Usuario o contraseña inválidos")

        # El rol enviado es solo informativo; no bloqueamos si no coincide.
        # Se usa el rol real del usuario para generar el token.
        
        # Build display name suffix based on role
        role_map = {
            "ADMIN": "AD",
            "CAMARERO": "ME",
        }
        role_code = role_map.get(user.role, user.role[:2].upper())
        display_name = f"{user.username}_{role_code}"

        # Create tokens and include display_name in token payload
        access_token = create_access_token({
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "display_name": display_name,
        })

        refresh_token = create_refresh_token({
            "sub": str(user.id),
            "username": user.username,
            "display_name": display_name,
        })

        return user, access_token, refresh_token, display_name


class GetUserUseCase:
    """Use case for getting user information."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def execute(self, user_id: int) -> User:
        """Get user by ID."""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValidationException("Usuario no encontrado")
        return user


class ListUsersUseCase:
    """Use case for listing users."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def execute(self, skip: int = 0, limit: int = 10) -> list[User]:
        """List users."""
        return await self.user_repository.list(skip, limit)


class UpdateUserUseCase:
    """Use case for updating user."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def execute(self, user_id: int, full_name: Optional[str] = None, phone: Optional[str] = None, is_active: Optional[bool] = None, updated_by: Optional[int] = None) -> User:
        """Update user."""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValidationException("Usuario no encontrado")
        
        # Update user
        user.full_name = full_name or user.full_name
        user.phone = phone if phone is not None else user.phone
        user.is_active = is_active if is_active is not None else user.is_active
        user.updated_by = updated_by
        
        return await self.user_repository.update(user_id, user)


class DeleteUserUseCase:
    """Use case for deleting user."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def execute(self, user_id: int) -> bool:
        """Delete user."""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValidationException("Usuario no encontrado")
        return await self.user_repository.delete(user_id)


class AdminUpdateUserUseCase:
    """Use case for admin updating any user fields."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: int, username: Optional[str] = None, email: Optional[str] = None,
                      password: Optional[str] = None, full_name: Optional[str] = None,
                      role: Optional[str] = None, is_active: Optional[bool] = None,
                      phone: Optional[str] = None, updated_by: Optional[int] = None) -> User:
        """Admin updates user with provided fields."""
        # Fetch user (including deleted to allow re-activating)
        existing = await self.user_repository.get_by_id(user_id, include_deleted=True)
        if not existing:
            raise ValidationException("Usuario no encontrado")

        # Check unique constraints
        if username and username != existing.username:
            other = await self.user_repository.get_by_username(username)
            if other and other.id != user_id:
                raise DuplicateResourceException(f"El usuario '{username}' ya existe")

        if email and email != existing.email:
            other = await self.user_repository.get_by_email(email)
            if other and other.id != user_id:
                raise DuplicateResourceException(f"El email '{email}' ya está registrado")

        # Prepare domain user with updates
        password_hash = None
        if password:
            password_hash = hash_password(password)

        user = User(
            id=user_id,
            username=username or existing.username,
            email=email or existing.email,
            password_hash=password_hash or existing.password_hash,
            full_name=full_name or existing.full_name,
            role=role or existing.role,
            is_active=is_active if is_active is not None else existing.is_active,
            phone=phone if phone is not None else existing.phone,
            updated_by=updated_by,
        )

        return await self.user_repository.update(user_id, user)


class RestoreUserUseCase:
    """Use case for restoring a user."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: int, restored_by: Optional[int] = None) -> User:
        """Restore a soft-deleted user."""
        user = await self.user_repository.get_by_id(user_id, include_deleted=True)
        if not user:
            raise ValidationException("Usuario no encontrado")
        if user.deleted_at is None:
            raise ValidationException("El usuario ya está activo")

        user.updated_by = restored_by
        return await self.user_repository.restore(user)


class ListUsersByRoleUseCase:
    """Use case for listing users by role."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def execute(self, role: str, skip: int = 0, limit: int = 10) -> list[User]:
        """List users by role."""
        # Validate role
        valid_roles = [r.value for r in UserRole]
        if role not in valid_roles:
            raise ValidationException(f"Rol inválido. Roles válidos: {', '.join(valid_roles)}")
        
        return await self.user_repository.get_by_role(role, skip, limit)
