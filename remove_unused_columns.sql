-- Script SQL para remover colunas desnecessárias das tabelas
-- Execute este script no Editor SQL do Supabase

-- 1. Verificar estrutura atual das tabelas
SELECT 'Estrutura atual da tabela molecules:' as info;
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'molecules' 
ORDER BY ordinal_position;

SELECT 'Estrutura atual da tabela calculations:' as info;
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'calculations' 
ORDER BY ordinal_position;

-- 2. Remover coluna formula da tabela molecules
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'molecules' 
        AND column_name = 'formula'
    ) THEN
        ALTER TABLE public.molecules DROP COLUMN formula;
        RAISE NOTICE 'Coluna formula removida da tabela molecules';
    ELSE
        RAISE NOTICE 'Coluna formula não existe na tabela molecules';
    END IF;
END
$$;

-- 3. Remover coluna pubchem_cid da tabela molecules
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'molecules' 
        AND column_name = 'pubchem_cid'
    ) THEN
        ALTER TABLE public.molecules DROP COLUMN pubchem_cid;
        RAISE NOTICE 'Coluna pubchem_cid removida da tabela molecules';
    ELSE
        RAISE NOTICE 'Coluna pubchem_cid não existe na tabela molecules';
    END IF;
END
$$;

-- 4. Remover coluna completed_at da tabela calculations
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'calculations' 
        AND column_name = 'completed_at'
    ) THEN
        ALTER TABLE public.calculations DROP COLUMN completed_at;
        RAISE NOTICE 'Coluna completed_at removida da tabela calculations';
    ELSE
        RAISE NOTICE 'Coluna completed_at não existe na tabela calculations';
    END IF;
END
$$;

-- 5. Verificar estrutura final das tabelas
SELECT 'Estrutura final da tabela molecules:' as info;
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'molecules' 
ORDER BY ordinal_position;

SELECT 'Estrutura final da tabela calculations:' as info;
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'calculations' 
ORDER BY ordinal_position;

-- 6. Teste simples para verificar que as tabelas ainda funcionam
DO $$
DECLARE
    test_molecule_id UUID;
    test_calculation_id UUID;
BEGIN
    -- Teste inserção na tabela molecules (sem pubchem_cid e formula)
    INSERT INTO public.molecules (name, enthalpy_formation_mopac, enthalpy_formation_mopac_kj) 
    VALUES ('test_no_columns', -100.5, -420.8) 
    RETURNING id INTO test_molecule_id;
    
    -- Teste inserção na tabela calculations (sem completed_at)
    INSERT INTO public.calculations (molecule_id, calculation_type, status, parameters) 
    VALUES (test_molecule_id, 'test', 'completed', '{}') 
    RETURNING id INTO test_calculation_id;
    
    -- Remove os dados de teste
    DELETE FROM public.calculations WHERE id = test_calculation_id;
    DELETE FROM public.molecules WHERE id = test_molecule_id;
    
    RAISE NOTICE 'TESTE CONCLUÍDO COM SUCESSO! As tabelas funcionam sem as colunas removidas.';
EXCEPTION
    WHEN OTHERS THEN
        -- Limpar em caso de erro
        DELETE FROM public.calculations WHERE molecule_id = test_molecule_id;
        DELETE FROM public.molecules WHERE name = 'test_no_columns';
        
        RAISE NOTICE 'ERRO NO TESTE: %', SQLERRM;
        RAISE;
END
$$;

-- Fim do script
