from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, BigIntPK


class Subject(Base):
    __tablename__ = "ast_subject"
    __table_args__ = (
        UniqueConstraint("domain_code", "subject_code", name="uq_ast_subject_domain_code"),
        {"comment": "业务过程（域内主题）"},
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True, comment="主键ID")
    domain_code: Mapped[str] = mapped_column(String(8), nullable=False, comment="所属数据域")
    subject_code: Mapped[str] = mapped_column(String(32), nullable=False, comment="业务过程编码")
    subject_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="业务过程名称")
    description: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="说明")
    sort: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")
