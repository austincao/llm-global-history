Process global history text (Stavrianos) and extract structured entity-relation data. Maintain strict JSON for downstream processing.

# Context
- Book: A Global History (全球通史), world-history perspective
- Chapter 22 covers Iberian expansion (1500–1600): Spain, Portugal, exploration, colonization
- Time format: use explicit years, e.g. `1415年`, `1500—1600年`, `16世纪`; BCE as `前403年` if applicable

# Steps
1. **Entity Identification**
- Extract persons, polities, civilizations, religions, organizations, schools
- **entity_type**: `person` | `polity` | `civilization` | `religion` | `organization` | `school`
- Record specific aliases only (not generic titles like `国王`, `the King`, `探险家`)
- For polities: Spain/葡萄牙/西班牙/奥斯曼帝国 etc.
- For civilization: Western Europe, Islamic world, etc. when used as civilizational actors
- **sentence_indexes_in_segment**: indexes from input `target_sentences`

2. **Location Identification**
- Cities, regions, seas, routes, colonies, straits
- Include `modern_name` when known (e.g. 休达/Ceuta)
- **sentence_indexes_in_segment** required

3. **Event Identification**
- Major expeditions, battles, treaties, discoveries, colonization milestones
- **time**, **location**, **participants** must cross-reference lists
- **background** and **significance** from model knowledge

4. **Relation Mapping (Action)**
- Political, military, religious, economic relations
- **from_roles** / **to_roles** must exist in entities
- **is_commentary**: true for quoted opinions (e.g. Adam Smith quote), false for historical facts
- **time** as stated in text or null

# Output Format
Output strict JSON only. No markdown outside the JSON block.
```json
{
  "entities": [
    {
      "entity_type": "person|polity|civilization|religion|organization|school",
      "name": "名称",
      "alias": [],
      "original_description_in_book": "原文描述",
      "description": "背景补充",
      "power": "所属势力或null",
      "sentence_indexes_in_segment": [0]
    }
  ],
  "locations": [
    {
      "name": "地点",
      "alias": [],
      "type": "城市|地区|海洋|海峡|殖民地等",
      "description": "描述",
      "modern_name": "现代地名或空",
      "related_entities": [],
      "sentence_indexes_in_segment": [0]
    }
  ],
  "events": [
    {
      "name": "事件名",
      "time": "时间或null",
      "location": "地点或null",
      "participants": [],
      "description": "描述",
      "background": "背景",
      "significance": "意义",
      "sentence_indexes_in_segment": [0]
    }
  ],
  "relations": [
    {
      "time": "时间或null",
      "from_roles": [],
      "to_roles": [],
      "action": "动作",
      "context": "背景",
      "result": "结果或null",
      "event_name": "事件名或null",
      "location": "地点或null",
      "is_commentary": false,
      "sentence_indexes_in_segment": [0]
    }
  ]
}
```

# Rules
- Do NOT merge different people with the same first name
- Do NOT use country names as aliases for persons
- Prefer canonical Chinese names from the text; add English names as alias when mentioned
- Extract ALL significant entities in target sentences; do not skip explorers, monarchs, or polities
