"""Tests for global history entity resolution."""

from entity_resolution import EntityResolver, normalize_event_name
from model.role import Role


def test_merge_columbus_aliases():
    resolver = EntityResolver()
    r1 = Role(name="克里斯托弗·哥伦布", alias=["哥伦布"], entity_type="person")
    r2 = Role(name="哥伦布", alias=["Christopher Columbus"], entity_type="person")
    resolver.add_role(r1, 22, 1, 0)
    resolver.add_role(r2, 22, 1, 5)
    kb = resolver.build_knowledge_base()
    assert kb.total_roles == 1
    role = next(iter(kb.roles.values()))
    assert "哥伦布" in role.all_names
    assert "克里斯托弗·哥伦布" in role.all_names


def test_polity_not_merged_with_person():
    resolver = EntityResolver()
    resolver.add_role(Role(name="葡萄牙", entity_type="polity"), 22, 1, 0)
    resolver.add_role(Role(name="亨利王子", entity_type="person", power="葡萄牙"), 22, 1, 1)
    kb = resolver.build_knowledge_base()
    assert kb.total_polities == 1
    assert kb.total_roles == 1


def test_event_name_normalization():
    assert normalize_event_name("哥伦布发现美洲") == "哥伦布首航发现美洲"
    assert normalize_event_name("攻占休达") == "攻占休达"


def test_blocked_generic_king_not_in_roles():
    resolver = EntityResolver()
    resolver.add_role(Role(name="国王", entity_type="person"), 22, 1, 0)
    resolver.add_role(Role(name="斐迪南", alias=["国王"], entity_type="person"), 22, 1, 1)
    kb = resolver.build_knowledge_base()
    assert "国王" not in kb.name_to_entity_id
    assert kb.total_roles == 1
