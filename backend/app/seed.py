"""
Database initial seed script for Boho
Can be invoked independently to pre-populate rules and initial test simulation.
"""
from app.database import engine, Base, SessionLocal
from app.models.firewall import FirewallRule
from app.api.rules import seed_default_rules


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        rules = seed_default_rules(db)
        print(f"Successfully initialized Boho database with {len(rules)} default firewall rules.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
