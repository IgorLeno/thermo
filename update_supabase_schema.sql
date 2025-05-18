-- Script SQL para adicionar o campo de entalpia em kJ/mol na tabela mopac_results
-- Execute este script no Editor SQL do Supabase

-- Verifica se a coluna já existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'mopac_results' 
        AND column_name = 'enthalpy_formation_kj'
    ) THEN
        -- Adiciona a coluna se ela não existir
        ALTER TABLE public.mopac_results ADD COLUMN enthalpy_formation_kj REAL;
        
        -- Comentário para documentação
        COMMENT ON COLUMN public.mopac_results.enthalpy_formation_kj IS 'Entalpia de formação em kJ/mol';
    END IF;
END
$$;

-- Informa o resultado da operação
SELECT EXISTS (
    SELECT 1 
    FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'mopac_results' 
    AND column_name = 'enthalpy_formation_kj'
) as "Coluna enthalpy_formation_kj existe";
