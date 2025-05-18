-- Script Final para Testar Sincronização no Supabase
-- Execute este script completo no Editor SQL do Supabase

-- 1. Verificar status das tabelas
SELECT 
    table_name,
    row_security
FROM information_schema.tables 
WHERE table_schema = 'public' 
    AND table_name IN ('molecules', 'calculations', 'crest_results', 'mopac_results');

-- 2. Verificar se as colunas necessárias existem
SELECT 
    table_name, 
    column_name, 
    data_type 
FROM information_schema.columns 
WHERE table_schema = 'public' 
    AND table_name IN ('molecules', 'mopac_results')
    AND column_name IN ('enthalpy_formation_mopac', 'enthalpy_formation_mopac_kj', 'enthalpy_formation_kj')
ORDER BY table_name, column_name;

-- 3. Se necessário, adicionar colunas que podem estar faltando
-- Coluna para entalpia em kcal/mol na tabela molecules
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'molecules' 
        AND column_name = 'enthalpy_formation_mopac'
    ) THEN
        ALTER TABLE public.molecules ADD COLUMN enthalpy_formation_mopac REAL;
        COMMENT ON COLUMN public.molecules.enthalpy_formation_mopac IS 'Entalpia de formação em kcal/mol (MOPAC)';
    END IF;
END
$$;

-- Coluna para entalpia em kJ/mol na tabela molecules
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'molecules' 
        AND column_name = 'enthalpy_formation_mopac_kj'
    ) THEN
        ALTER TABLE public.molecules ADD COLUMN enthalpy_formation_mopac_kj REAL;
        COMMENT ON COLUMN public.molecules.enthalpy_formation_mopac_kj IS 'Entalpia de formação em kJ/mol (MOPAC)';
    END IF;
END
$$;

-- 4. Reconfirmar que o RLS está desativado
ALTER TABLE public.molecules DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.calculations DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.crest_results DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.mopac_results DISABLE ROW LEVEL SECURITY;

-- 5. Garantir permissões completas
GRANT ALL PRIVILEGES ON public.molecules TO anon, authenticated, service_role;
GRANT ALL PRIVILEGES ON public.calculations TO anon, authenticated, service_role;
GRANT ALL PRIVILEGES ON public.crest_results TO anon, authenticated, service_role;
GRANT ALL PRIVILEGES ON public.mopac_results TO anon, authenticated, service_role;

-- Permissões nas sequências
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role;

-- 6. Teste de inserção completamente seguro
DO $$
DECLARE
    test_molecule_id UUID;
    test_calculation_id UUID;
BEGIN
    -- Tenta inserir uma molécula de teste
    INSERT INTO public.molecules (name, pubchem_cid, enthalpy_formation_mopac, enthalpy_formation_mopac_kj) 
    VALUES ('test_sync_molecule', 99999, -100.5, -420.8) 
    RETURNING id INTO test_molecule_id;
    
    -- Tenta inserir um cálculo de teste
    INSERT INTO public.calculations (molecule_id, calculation_type, status, parameters) 
    VALUES (test_molecule_id, 'test', 'completed', '{}') 
    RETURNING id INTO test_calculation_id;
    
    -- Tenta inserir resultados MOPAC de teste
    INSERT INTO public.mopac_results (calculation_id, enthalpy_formation, enthalpy_formation_kj, method) 
    VALUES (test_calculation_id, -100.5, -420.8, 'PM7');
    
    -- Remove os dados de teste
    DELETE FROM public.mopac_results WHERE calculation_id = test_calculation_id;
    DELETE FROM public.calculations WHERE id = test_calculation_id;
    DELETE FROM public.molecules WHERE id = test_molecule_id;
    
    RAISE NOTICE 'TESTE CONCLUÍDO COM SUCESSO! Todas as tabelas estão acessíveis.';
EXCEPTION
    WHEN OTHERS THEN
        -- Remove dados de teste em caso de erro
        DELETE FROM public.mopac_results WHERE calculation_id = test_calculation_id;
        DELETE FROM public.calculations WHERE id = test_calculation_id;
        DELETE FROM public.molecules WHERE name = 'test_sync_molecule';
        
        RAISE NOTICE 'ERRO NO TESTE: %', SQLERRM;
        RAISE;
END
$$;

-- 7. Verificação final do status
SELECT 
    'Verificação Final' as status,
    table_name,
    CASE WHEN row_security THEN 'RLS ATIVO (PODE CAUSAR PROBLEMAS)' ELSE 'RLS DESATIVADO (OK)' END as security_status
FROM information_schema.tables 
WHERE table_schema = 'public' 
    AND table_name IN ('molecules', 'calculations', 'crest_results', 'mopac_results')
ORDER BY table_name;

-- 8. Contagem atual de registros
SELECT 'molecules' as table_name, COUNT(*) as total_records FROM public.molecules
UNION ALL
SELECT 'calculations' as table_name, COUNT(*) as total_records FROM public.calculations
UNION ALL  
SELECT 'crest_results' as table_name, COUNT(*) as total_records FROM public.crest_results
UNION ALL
SELECT 'mopac_results' as table_name, COUNT(*) as total_records FROM public.mopac_results;

-- Fim do script. Se chegou até aqui sem erros, a sincronização deve funcionar!
