-- Script SQL para adicionar as colunas de entalpia na tabela molecules
-- Execute este script no Editor SQL do Supabase

-- 1. Verificar estrutura atual da tabela molecules
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'molecules' 
ORDER BY ordinal_position;

-- 2. Adicionar coluna para entalpia em kcal/mol
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
        RAISE NOTICE 'Coluna enthalpy_formation_mopac adicionada com sucesso';
    ELSE
        RAISE NOTICE 'Coluna enthalpy_formation_mopac já existe';
    END IF;
END
$$;

-- 3. Adicionar coluna para entalpia em kJ/mol
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
        RAISE NOTICE 'Coluna enthalpy_formation_mopac_kj adicionada com sucesso';
    ELSE
        RAISE NOTICE 'Coluna enthalpy_formation_mopac_kj já existe';
    END IF;
END
$$;

-- 4. Verificar se as colunas foram criadas corretamente
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'molecules' 
AND column_name IN ('enthalpy_formation_mopac', 'enthalpy_formation_mopac_kj');

-- 5. Verificar nova estrutura da tabela molecules
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'molecules' 
ORDER BY ordinal_position;

-- 6. Teste simples para verificar se as colunas funcionam
DO $$
DECLARE
    test_id UUID;
BEGIN
    -- Inserir um registro de teste
    INSERT INTO public.molecules (name, pubchem_cid, enthalpy_formation_mopac, enthalpy_formation_mopac_kj) 
    VALUES ('test_molecule_columns', 123456, -100.5, -420.8) 
    RETURNING id INTO test_id;
    
    -- Verificar se os dados foram inseridos
    IF EXISTS (SELECT 1 FROM public.molecules WHERE id = test_id) THEN
        RAISE NOTICE 'TESTE CONCLUÍDO COM SUCESSO! As colunas estão funcionando.';
    END IF;
    
    -- Remover o registro de teste
    DELETE FROM public.molecules WHERE id = test_id;
    
EXCEPTION
    WHEN OTHERS THEN
        -- Limpar em caso de erro
        DELETE FROM public.molecules WHERE name = 'test_molecule_columns';
        RAISE NOTICE 'ERRO NO TESTE: %', SQLERRM;
        RAISE;
END
$$;

-- Fim do script
