from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, BigIntPK


class PreviewAudit(Base):
    """数据预览审计记录。"""

    __tablename__ = "ast_preview_audit"
    __table_args__ = {"comment": "数据预览审计"}

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="用户ID")
    username: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="用户名")
    object_type: Mapped[str] = mapped_column(String(16), nullable=False, comment="对象类型（RESOURCE/ASSET）")
    object_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="对象ID")
    schema_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="schema 名")
    table_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="表名")
    columns_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="查询列（逗号分隔）")
    row_limit: Mapped[int] = mapped_column(Integer, default=20, comment="请求行数")
    row_returned: Mapped[int] = mapped_column(Integer, default=0, comment="返回行数")
    masked: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用脱敏")
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="客户端IP")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="预览时间")
