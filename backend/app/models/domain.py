from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, BigIntPK


class Domain(Base):
    __tablename__ = "ast_domain"
    __table_args__ = {"comment": "数据域（10 域固定规划）"}

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    domain_code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False, comment="域码")
    domain_name: Mapped[str] = mapped_column(String(32), nullable=False, comment="数据域中文名")
    sampled: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已打样")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="边界说明")
    anchor_x: Mapped[float | None] = mapped_column(Float, nullable=True, comment="地图锚点X(0-1)")
    anchor_y: Mapped[float | None] = mapped_column(Float, nullable=True, comment="地图锚点Y(0-1)")
