-- Script para adicionar colunas relacionadas ao Chemperium na tabela molecules
-- Execute este script no Editor SQL do Supabase para adicionar os novos campos

-- Adiciona coluna para SMILES (se não existir)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'molecules' AND column_name = 'smiles') THEN
        ALTER TABLE molecules ADD COLUMN smiles TEXT;
        RAISE NOTICE 'Coluna smiles adicionada';
    ELSE
        RAISE NOTICE 'Coluna smiles já existe';
    END IF;
END $$;

-- Adiciona coluna para entalpia Chemperium (se não existir)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'molecules' AND column_name = 'hf_chemp') THEN
        ALTER TABLE molecules ADD COLUMN hf_chemp DECIMAL;
        RAISE NOTICE 'Coluna hf_chemp adicionada';
    ELSE
        RAISE NOTICE 'Coluna hf_chemp já existe';
    END IF;
END $$;

-- Adiciona coluna para incerteza Chemperium (se não existir)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'molecules' AND column_name = 'hf_chemp_uncertainty') THEN
        ALTER TABLE molecules ADD COLUMN hf_chemp_uncertainty DECIMAL;
        RAISE NOTICE 'Coluna hf_chemp_uncertainty adicionada';
    ELSE
        RAISE NOTICE 'Coluna hf_chemp_uncertainty já existe';
    END IF;
END $$;

-- Adiciona coluna para score de confiabilidade Chemperium (se não existir)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'molecules' AND column_name = 'chemperium_reliability') THEN
        ALTER TABLE molecules ADD COLUMN chemperium_reliability DECIMAL;
        RAISE NOTICE 'Coluna chemperium_reliability adicionada';
    ELSE
        RAISE NOTICE 'Coluna chemperium_reliability já existe';
    END IF;
END $$;

-- Adiciona comentários nas colunas para documentação
COMMENT ON COLUMN molecules.smiles IS 'SMILES canônico da molécula obtido do PubChem';
COMMENT ON COLUMN molecules.hf_chemp IS 'Entalpia de formação corrigida pelo Chemperium (kJ/mol)';
COMMENT ON COLUMN molecules.hf_chemp_uncertainty IS 'Incerteza da predição Chemperium (kJ/mol)';
COMMENT ON COLUMN molecules.chemperium_reliability IS 'Score de confiabilidade do Chemperium (0-1)';

-- Verifica se as colunas foram criadas
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'molecules' 
  AND column_name IN ('smiles', 'hf_chemp', 'hf_chemp_uncertainty', 'chemperium_reliability')
ORDER BY column_name;

RAISE NOTICE 'Script de adição de colunas Chemperium executado com sucesso!';
