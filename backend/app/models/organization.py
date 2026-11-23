from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, BigIntPK


class Organization(Base):
    __tablename__ = "sys_organization"
    __table_args__ = {"comment": "组织架构"}

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, comment="组织编码")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="组织名称")
    parent_id: Mapped[int | None] = mapped_column(
        BigIntPK, ForeignKey("sys_organization.id"), nullable=True, comment="上级组织ID"
    )
    type: Mapped[str] = mapped_column(
        String(16), nullable=False, comment="组织类型（GROUP集团/WATER_COMPANY水司/BIZ_OFFICE营业所/PLANT水厂）"
    )
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")

    parent: Mapped["Organization | None"] = relationship(
        "Organization", remote_side=[id], backref="children"
    )
