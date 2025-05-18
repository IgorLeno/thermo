-- Script SQL para corrigir as políticas de segurança (RLS) no Supabase
-- Execute este script no Editor SQL do Supabase

-- Desativar temporariamente a proteção RLS para permitir a inserção de dados
ALTER TABLE public.molecules DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.calculations DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.crest_results DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.mopac_results DISABLE ROW LEVEL SECURITY;

-- Alternativa: Se você preferir manter a RLS ativada, mas permitir que o usuário anônimo insira dados
-- CREATE POLICY "Allow anonymous inserts" ON public.molecules FOR INSERT TO anon WITH CHECK (true);
-- CREATE POLICY "Allow anonymous inserts" ON public.calculations FOR INSERT TO anon WITH CHECK (true);
-- CREATE POLICY "Allow anonymous inserts" ON public.crest_results FOR INSERT TO anon WITH CHECK (true);
-- CREATE POLICY "Allow anonymous inserts" ON public.mopac_results FOR INSERT TO anon WITH CHECK (true);

-- Certificar-se de que o papel anônimo tenha permissões corretas
GRANT ALL ON public.molecules TO anon;
GRANT ALL ON public.calculations TO anon;
GRANT ALL ON public.crest_results TO anon;
GRANT ALL ON public.mopac_results TO anon;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO anon;

-- Certifique-se de que as tabelas existem e têm a estrutura correta
-- Se alguma tabela não existir ou estiver com estrutura incompatível, isto ajudará a diagnosticar
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'molecules'
);

SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'calculations'
);

SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'crest_results'
);

SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'mopac_results'
);
