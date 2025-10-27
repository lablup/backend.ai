**최종 목표**
- UserNode의 `get_connection` 리졸버에 project name을 바탕으로 user를 필터링하는 로직을 추가하고 싶습니다

**배경**
- 현재 구조의 경우 `get_connection`리졸버에 인자로 들어온 str 형태의 filter_expr를  _queryfilter_fieldspec에 있는 필터 스펙을 바탕으로 Lark로 AST를 만들고, 이를 통해 SQL문을 `generate_sql_info_for_gql_connection`을 만드는 구조로 되어있습니다
- 하지만 _queryfilter_fieldspec으로 만든 AST로 SQL을 만드는 현재 플로우의 경우 UserNode가 사용하는 users 테이블에 있는 컬럼(`src/ai/backend/manager/models/user.py`에 UserRow 참고)에 있는 것들에 대해서만 필터링을 한다는 것을 가정하고 만들어졌습니다.
- Project의 name의 경우 GroupRow에 있고, User와 Group은 AssocGroupUserRow라는 중간 테이블을 매개로 N:N 관계를 맺고 있습니다

**구현**
- _queryfilter_fieldspec은 UserRow에 있는 테이블 정보를 반영한다고 생각하고, 별도의 테이블에서 가져오는 스펙을 만들고 이를 바탕으로 필터링하는 로직을 만들어주세요
- join 쿼리는 아래를 참고하면 테이블 구조를 대강 알 수 있을 겁니다
```python
j = sa.join(
    UserRow,
    AssocGroupUserRow,
    UserRow.uuid == AssocGroupUserRow.user_id,
).join(GroupRow, AssocGroupUserRow.group_id == GroupRow.id)

query = query.select_from(j).where(project_name_filter_clause).distinct()

cnt_query = sa.select(sa.func.count(sa.distinct(UserRow.uuid))).select_from(j)
cnt_query = cnt_query.where(project_name_filter_clause)
for cond in conditions:
    cnt_query = cnt_query.where(cond)
```
- 쿼리를 최대한 효율적으로 작성해주세요. AND나 OR이 걸렸을 때 또 JOIN하지 않도록 해주세요. 아니면 아예 일관성있게 비효율적으로 처음부터 join을 박거나 하는 방법도 좋습니다 (if 분기타면서 join하거나 그런 유지보수가 힘든 쿼리를 만들지 말라는 뜻)


**유의사항**
- 구현이 더럽더라도(Table에 대한 정보를 GQL이라는 API 레이어에서 알고 있는 것) 상관없습니다. 어짜피 Graphene으로 작성된 것은 Strawberry로 넘어가면서 새로 작성할 것이기 때문입니다
- 다만 UserNode의 경우에도 이후 `src/ai/backend/manager/api/gql/artifact.py`의 resolve_artifacts 함수처럼 filter나 OrderBy 객체를 만들고, 이를 서비스 레이어에 넘기는 방식으로 리팩토링 할 것입니다.
- 현재 UserNode가 ArtifactFilter 처럼 Filter, Order 객체를 만들어서 넘기는 등의 대대적인 개편을 하지는 마세요. 다만 이후 그렇게 넘어가기 쉽도록 다른 테이블의 컬럼을 바탕으로 필터링하는 로직을 설계해주세요