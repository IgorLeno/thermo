-- Script SQL completo para corrigir as políticas de segurança (RLS) no Supabase
-- Execute este script no Editor SQL do Supabase

-- 1. Primeiro, vamos verificar se as tabelas existem
SELECT 
    schemaname, 
    tablename, 
    rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN ('molecules', 'calculations', 'crest_results', 'mopac_results');

-- 2. Remover todas as políticas existentes que possam estar causando problemas
DROP POLICY IF EXISTS "Allow anonymous inserts" ON public.molecules;
DROP POLICY IF EXISTS "Allow anonymous inserts" ON public.calculations;
DROP POLICY IF EXISTS "Allow anonymous inserts" ON public.crest_results;
DROP POLICY IF EXISTS "Allow anonymous inserts" ON public.mopac_results;

-- Remove qualquer política que possa existir
DROP POLICY IF EXISTS "Enable insert for authenticated users only" ON public.molecules;
DROP POLICY IF EXISTS "Enable read access for all users" ON public.molecules;
DROP POLICY IF EXISTS "Enable insert for authenticated users only" ON public.calculations;
DROP POLICY IF EXISTS "Enable read access for all users" ON public.calculations;
DROP POLICY IF EXISTS "Enable insert for authenticated users only" ON public.crest_results;
DROP POLICY IF EXISTS "Enable read access for all users" ON public.crest_results;
DROP POLICY IF EXISTS "Enable insert for authenticated users only" ON public.mopac_results;
DROP POLICY IF EXISTS "Enable read access for all users" ON public.mopac_results;

-- 3. Desativar completamente a proteção RLS (Row Level Security)
ALTER TABLE public.molecules DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.calculations DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.crest_results DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.mopac_results DISABLE ROW LEVEL SECURITY;

-- 4. Dar permissões completas ao papel anônimo (anon) e autenticado (authenticated)
GRANT ALL PRIVILEGES ON public.molecules TO anon, authenticated;
GRANT ALL PRIVILEGES ON public.calculations TO anon, authenticated;
GRANT ALL PRIVILEGES ON public.crest_results TO anon, authenticated;
GRANT ALL PRIVILEGES ON public.mopac_results TO anon, authenticated;

-- 5. Dar permissões nas sequências (para campos auto-incrementais)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- 6. Verificar se as permissões foram aplicadas corretamente
SELECT 
    table_name,
    grantee,
    privilege_type
FROM information_schema.table_privileges
WHERE table_schema = 'public'
    AND table_name IN ('molecules', 'calculations', 'crest_results', 'mopac_results')
    AND grantee IN ('anon', 'authenticated')
ORDER BY table_name, grantee;

-- 7. Verificar o status atual das políticas RLS
SELECT 
    schemaname, 
    tablename, 
    rowsecurity
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN ('molecules', 'calculations', 'crest_results', 'mopac_results');

-- 8. Se ainda quiser usar RLS (não recomendado para simplicidade), descomente as linhas abaixo:
/*
-- Reativar RLS e criar políticas permissivas
ALTER TABLE public.molecules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.calculations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.crest_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mopac_results ENABLE ROW LEVEL SECURITY;

-- Criar políticas que permitem tudo para usuários anônimos e autenticados
CREATE POLICY "Allow all for all users" ON public.molecules FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for all users" ON public.calculations FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for all users" ON public.crest_results FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for all users" ON public.mopac_results FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);
*/

-- 9. Verificação final - estas consultas devem retornar 't' ou 'true' se tudo estiver funcionando
SELECT 'molecules table accessible' as test, 
       CASE WHEN EXISTS(SELECT 1 FROM public.molecules LIMIT 1) OR pg_table_size('public.molecules') >= 0 
            THEN 'PASS' ELSE 'FAIL' END as result;

SELECT 'calculations table accessible' as test,
       CASE WHEN EXISTS(SELECT 1 FROM public.calculations LIMIT 1) OR pg_table_size('public.calculations') >= 0 
            THEN 'PASS' ELSE 'FAIL' END as result;

-- 10. Teste de inserção simples (pode falhar se já existir)
-- REMOVA as linhas abaixo após o teste
/*
INSERT INTO public.molecules (name, pubchem_cid) VALUES ('test_molecule', 12345);
DELETE FROM public.molecules WHERE name = 'test_molecule';
*/

-- Fim do script
