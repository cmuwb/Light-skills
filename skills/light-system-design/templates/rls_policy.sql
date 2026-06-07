-- PostgreSQL 行级安全 (RLS) 骨架（多租户起手模板）
-- 约定要点见 ../references.md 与 SKILL.md「安全与运维 / 行级安全」段。
-- 配合 schema.sql 使用；落地前用真实角色跑通再上线。

-- 1. 开启 RLS（开启后默认拒绝所有访问，必须显式加 policy）
alter table app_user enable row level security;

-- 2. 分操作写 policy，永远写 to 子句（限定角色，别让 policy 对所有角色生效）
-- select：用户只能看本租户数据
create policy app_user_select on app_user
    for select to authenticated
    using (tenant_id = (select auth.tenant_id()));   -- 函数包进 select 触发 initPlan 缓存，避免逐行求值

-- insert：只能往自己租户插
create policy app_user_insert on app_user
    for insert to authenticated
    with check (tenant_id = (select auth.tenant_id()));

-- update：只能改自己租户，且改完仍属本租户
create policy app_user_update on app_user
    for update to authenticated
    using (tenant_id = (select auth.tenant_id()))
    with check (tenant_id = (select auth.tenant_id()));

-- 3. policy 引用的列要建索引（否则每行求值走全表扫）
create index if not exists idx_app_user_tenant_rls on app_user(tenant_id);

-- 性能与安全注意：
--   * 授权数据用 raw_app_meta_data（用户改不了），别用 raw_user_meta_data。
--   * 复杂跨表判断别在 policy 里 join，改子查询 IN，或封装成 security definer
--     函数放非暴露 schema，避免 RLS 递归与性能塌方。
--   * 验证：以目标角色 set role authenticated; 跑查询，确认只返回本租户行。
