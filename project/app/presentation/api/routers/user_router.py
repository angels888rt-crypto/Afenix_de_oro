"""User API routers."""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_session
from app.infrastructure.database.repositories import UserRepository
from app.application.use_cases.user_use_cases import (
    RegisterUserUseCase, LoginUserUseCase, GetUserUseCase, ListUsersUseCase,
    UpdateUserUseCase, DeleteUserUseCase, RestoreUserUseCase, ListUsersByRoleUseCase,
    AdminUpdateUserUseCase
)
from app.application.dto import (
    UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse, UserUpdateRequest
)
from app.application.dto import AdminUserUpdateRequest
from app.shared.responses import ResponseSchema
from app.presentation.api.dependencies.auth_dependencies import (
    get_user_repository, get_current_user, require_role, get_history_repository
)
from app.infrastructure.database.repositories import HistoryRepository

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


async def _log_history_safe(history_repo: HistoryRepository, **kwargs):
    try:
        await history_repo.create(**kwargs)
    except Exception:
        pass


@router.post("/register", response_model=ResponseSchema[UserResponse], status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    current_user: dict = Depends(get_current_user),
    user_repository: UserRepository = Depends(get_user_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
):
    """
    Register a new user.
    
    - **username**: Username (3-50 characters)
    - **password**: Password (minimum 8 characters)
    - **full_name**: Full name (3-100 characters)
    - **role**: User role (ADMIN, CAMARERO)
    - **phone**: Optional phone number
    """
    current_user = await require_role("ADMIN")(current_user)
    use_case = RegisterUserUseCase(user_repository)
    user = await use_case.execute(
        username=request.username,
        password=request.password,
        full_name=request.full_name,
        role=request.role,
        phone=request.phone,
    )
    await _log_history_safe(
        history_repo,
        category="USUARIOS",
        action="CREADO",
        entity_type="USUARIO",
        entity_id=user.id,
        entity_name=user.username,
        description=f"Usuario '{user.username}' creado (rol {user.role}, nombre: {user.full_name})",
        details={"username": user.username, "role": user.role, "full_name": user.full_name},
        performed_by=current_user["user_id"],
        performed_by_username=current_user.get("username"),
    )
    
    return ResponseSchema(
        success=True,
        message="Usuario registrado exitosamente",
        data=UserResponse(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            phone=user.phone,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
    )


@router.post("/login", response_model=ResponseSchema[TokenResponse])
async def login(
    request: UserLoginRequest,
    user_repository: UserRepository = Depends(get_user_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
):
    """
    Login user and get JWT tokens.
    
    Returns access_token and refresh_token.
    """
    use_case = LoginUserUseCase(user_repository)
    user, access_token, refresh_token, display_name = await use_case.execute(
        username=request.username,
        password=request.password,
        role=request.role,
    )

    await _log_history_safe(
        history_repo,
        category="LOGIN",
        action="LOGIN",
        entity_type="USUARIO",
        entity_id=user.id,
        entity_name=user.username,
        description=f"Inicio de sesión: usuario '{user.username}' (rol {user.role}) ingresó al sistema",
        details={"username": user.username, "role": user.role, "display_name": display_name},
        performed_by=user.id,
        performed_by_username=user.username,
    )

    return ResponseSchema(
        success=True,
        message="Autenticación exitosa",
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30 * 60,  # 30 minutes
            display_name=display_name,
            role=user.role,
        )
    )


@router.get("/me", response_model=ResponseSchema[UserResponse])
async def get_me(
    current_user: dict = Depends(get_current_user),
    user_repository: UserRepository = Depends(get_user_repository),
):
    """Get current user information."""
    use_case = GetUserUseCase(user_repository)
    user = await use_case.execute(current_user["user_id"])
    
    return ResponseSchema(
        success=True,
        message="Usuario obtenido exitosamente",
        data=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            phone=user.phone,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
    )


@router.get("/{user_id}", response_model=ResponseSchema[UserResponse])
async def get_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    user_repository: UserRepository = Depends(get_user_repository),
):
    """Get user by ID (admin only)."""
    current_user = await require_role("ADMIN")(current_user)
    use_case = GetUserUseCase(user_repository)
    user = await use_case.execute(user_id)
    
    return ResponseSchema(
        success=True,
        message="Usuario obtenido exitosamente",
        data=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            phone=user.phone,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
    )


@router.get("", response_model=ResponseSchema[list[UserResponse]])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    user_repository: UserRepository = Depends(get_user_repository),
):
    """List all users — cualquier usuario autenticado y activo puede consultar (para Auxiliares y recargas)."""
    # No exigimos rol ADMIN aquí; la sección Auxiliares debe ser accesible con cualquier rol válido.
    # Si se requiere restricción futura, se puede reintroducir require_role con lista más amplia.
    use_case = ListUsersUseCase(user_repository)
    users = await use_case.execute(skip, limit)
    
    return ResponseSchema(
        success=True,
        message="Usuarios obtenidos exitosamente",
        data=[
            UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active,
                phone=user.phone,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
            for user in users
        ]
    )


@router.put("/{user_id}", response_model=ResponseSchema[UserResponse])
async def update_user(
    user_id: int,
    request: UserUpdateRequest,
    current_user: dict = Depends(get_current_user),
    user_repository: UserRepository = Depends(get_user_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
):
    """Update user information."""
    # Users can only update their own info, admins can update anyone
    if current_user["user_id"] != user_id and current_user["role"] != "ADMIN":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="No tiene permiso para actualizar este usuario")
    
    use_case = UpdateUserUseCase(user_repository)
    user = await use_case.execute(
        user_id=user_id,
        full_name=request.full_name,
        phone=request.phone,
        is_active=request.is_active,
        updated_by=current_user["user_id"],
    )
    await _log_history_safe(
        history_repo,
        category="USUARIOS",
        action="ACTUALIZADO",
        entity_type="USUARIO",
        entity_id=user.id,
        entity_name=user.username,
        description=f"Usuario '{user.username}' actualizado (nombre: {user.full_name})",
        details={"updated_fields": request.model_dump(exclude_none=True)},
        performed_by=current_user["user_id"],
        performed_by_username=current_user.get("username"),
    )
    
    return ResponseSchema(
        success=True,
        message="Usuario actualizado exitosamente",
        data=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            phone=user.phone,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
    )


@router.put("/{user_id}/admin", response_model=ResponseSchema[UserResponse])
async def admin_update_user(
    user_id: int,
    request: AdminUserUpdateRequest,
    current_user: dict = Depends(get_current_user),
    user_repository: UserRepository = Depends(get_user_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
):
    """Admin updates any user fields (admin only)."""
    current_user = await require_role("ADMIN")(current_user)
    use_case = AdminUpdateUserUseCase(user_repository)
    user = await use_case.execute(
        user_id=user_id,
        username=request.username,
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        role=request.role,
        is_active=request.is_active,
        phone=request.phone,
        updated_by=current_user["user_id"],
    )
    await _log_history_safe(
        history_repo,
        category="USUARIOS",
        action="ACTUALIZADO",
        entity_type="USUARIO",
        entity_id=user.id,
        entity_name=user.username,
        description=f"Usuario '{user.username}' actualizado por admin (rol {user.role})",
        details={"updated_fields": request.model_dump(exclude_none=True)},
        performed_by=current_user["user_id"],
        performed_by_username=current_user.get("username"),
    )

    return ResponseSchema(
        success=True,
        message="Usuario actualizado por admin exitosamente",
        data=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            phone=user.phone,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    user_repository: UserRepository = Depends(get_user_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
):
    """Delete user (admin only)."""
    current_user = await require_role("ADMIN")(current_user)
    # capture info before delete
    target = await user_repository.get_by_id(user_id)
    use_case = DeleteUserUseCase(user_repository)
    await use_case.execute(user_id)
    if target:
        await _log_history_safe(
            history_repo,
            category="USUARIOS",
            action="ELIMINADO",
            entity_type="USUARIO",
            entity_id=user_id,
            entity_name=target.username,
            description=f"Usuario '{target.username}' eliminado (rol {target.role})",
            details={"username": target.username, "role": target.role},
            performed_by=current_user["user_id"],
            performed_by_username=current_user.get("username"),
        )


@router.put("/{user_id}/restore", response_model=ResponseSchema[UserResponse])
async def restore_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    user_repository: UserRepository = Depends(get_user_repository),
    history_repo: HistoryRepository = Depends(get_history_repository),
):
    """Restore a deleted user (admin only)."""
    current_user = await require_role("ADMIN")(current_user)
    use_case = RestoreUserUseCase(user_repository)
    user = await use_case.execute(user_id, restored_by=current_user["user_id"])
    await _log_history_safe(
        history_repo,
        category="USUARIOS",
        action="ACTUALIZADO",
        entity_type="USUARIO",
        entity_id=user.id,
        entity_name=user.username,
        description=f"Usuario '{user.username}' restaurado (rol {user.role})",
        details={"username": user.username, "role": user.role},
        performed_by=current_user["user_id"],
        performed_by_username=current_user.get("username"),
    )

    return ResponseSchema(
        success=True,
        message="Usuario restaurado exitosamente",
        data=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            phone=user.phone,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
    )


@router.get("/role/{role}", response_model=ResponseSchema[list[UserResponse]])
async def get_users_by_role(
    role: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    user_repository: UserRepository = Depends(get_user_repository),
):
    """Get users by role (admin only)."""
    current_user = await require_role("ADMIN")(current_user)
    use_case = ListUsersByRoleUseCase(user_repository)
    users = await use_case.execute(role, skip, limit)
    
    return ResponseSchema(
        success=True,
        message="Usuarios obtenidos exitosamente",
        data=[
            UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active,
                phone=user.phone,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
            for user in users
        ]
    )
