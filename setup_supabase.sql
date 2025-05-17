-- Script SQL para configurar o banco de dados Supabase
-- Use este script no Editor SQL do Supabase para criar as tabelas necessárias

-- Tabela para armazenar informações das moléculas
CREATE TABLE IF NOT EXISTS public.molecules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    pubchem_cid TEXT,
    formula TEXT,
    smiles TEXT,
    molecular_weight REAL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Comentários na tabela molecules
COMMENT ON TABLE public.molecules IS 'Tabela para armazenar informações das moléculas';
COMMENT ON COLUMN public.molecules.name IS 'Nome da molécula';
COMMENT ON COLUMN public.molecules.pubchem_cid IS 'Identificador no PubChem';
COMMENT ON COLUMN public.molecules.formula IS 'Fórmula molecular';
COMMENT ON COLUMN public.molecules.smiles IS 'Representação SMILES da estrutura';
COMMENT ON COLUMN public.molecules.molecular_weight IS 'Peso molecular em g/mol';

-- Tabela para armazenar informações dos cálculos
CREATE TABLE IF NOT EXISTS public.calculations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    molecule_id UUID NOT NULL REFERENCES public.molecules(id) ON DELETE CASCADE,
    calculation_type TEXT NOT NULL, -- 'crest' ou 'mopac'
    status TEXT NOT NULL, -- 'completed', 'failed', 'running', etc.
    parameters JSONB, -- Parâmetros específicos do cálculo
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Comentários na tabela calculations
COMMENT ON TABLE public.calculations IS 'Tabela para armazenar informações dos cálculos';
COMMENT ON COLUMN public.calculations.molecule_id IS 'Referência à molécula';
COMMENT ON COLUMN public.calculations.calculation_type IS 'Tipo de cálculo: crest, mopac, etc.';
COMMENT ON COLUMN public.calculations.status IS 'Status do cálculo: completed, failed, running, etc.';
COMMENT ON COLUMN public.calculations.parameters IS 'Parâmetros específicos do cálculo em formato JSON';

-- Tabela para armazenar resultados específicos do CREST
CREATE TABLE IF NOT EXISTS public.crest_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    calculation_id UUID NOT NULL REFERENCES public.calculations(id) ON DELETE CASCADE,
    num_conformers INTEGER,
    best_conformer_path TEXT,
    all_conformers_path TEXT,
    energy_distribution JSONB,
    relative_energies JSONB,
    populations JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Comentários na tabela crest_results
COMMENT ON TABLE public.crest_results IS 'Tabela para armazenar resultados da busca conformacional com CREST';
COMMENT ON COLUMN public.crest_results.calculation_id IS 'Referência ao cálculo';
COMMENT ON COLUMN public.crest_results.num_conformers IS 'Número de confôrmeros encontrados';
COMMENT ON COLUMN public.crest_results.best_conformer_path IS 'Caminho para o arquivo do melhor confôrmero';
COMMENT ON COLUMN public.crest_results.all_conformers_path IS 'Caminho para o arquivo com todos os confôrmeros';
COMMENT ON COLUMN public.crest_results.energy_distribution IS 'Distribuição de energia dos confôrmeros';
COMMENT ON COLUMN public.crest_results.relative_energies IS 'Energias relativas dos confôrmeros em kJ/mol';
COMMENT ON COLUMN public.crest_results.populations IS 'Populações dos confôrmeros baseadas na distribuição de Boltzmann';

-- Tabela para armazenar resultados específicos do MOPAC
CREATE TABLE IF NOT EXISTS public.mopac_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    calculation_id UUID NOT NULL REFERENCES public.calculations(id) ON DELETE CASCADE,
    enthalpy_formation REAL,
    method TEXT, -- PM7, PM6, AM1, etc.
    output_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Comentários na tabela mopac_results
COMMENT ON TABLE public.mopac_results IS 'Tabela para armazenar resultados dos cálculos de entalpia com MOPAC';
COMMENT ON COLUMN public.mopac_results.calculation_id IS 'Referência ao cálculo';
COMMENT ON COLUMN public.mopac_results.enthalpy_formation IS 'Entalpia de formação calculada (kcal/mol ou kJ/mol)';
COMMENT ON COLUMN public.mopac_results.method IS 'Método utilizado no cálculo (PM7, PM6, AM1, etc.)';
COMMENT ON COLUMN public.mopac_results.output_path IS 'Caminho para o arquivo de saída do MOPAC';

-- Criar índices para melhorar a performance das consultas
CREATE INDEX IF NOT EXISTS idx_molecules_name ON public.molecules(name);
CREATE INDEX IF NOT EXISTS idx_calculations_molecule_id ON public.calculations(molecule_id);
CREATE INDEX IF NOT EXISTS idx_calculations_type ON public.calculations(calculation_type);
CREATE INDEX IF NOT EXISTS idx_crest_results_calculation_id ON public.crest_results(calculation_id);
CREATE INDEX IF NOT EXISTS idx_mopac_results_calculation_id ON public.mopac_results(calculation_id);

-- Criar triggers para atualizar o campo updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar o trigger nas tabelas que possuem o campo updated_at
CREATE TRIGGER update_molecules_updated_at
BEFORE UPDATE ON public.molecules
FOR EACH ROW EXECUTE PROCEDURE update_updated_at();

CREATE TRIGGER update_crest_results_updated_at
BEFORE UPDATE ON public.crest_results
FOR EACH ROW EXECUTE PROCEDURE update_updated_at();

CREATE TRIGGER update_mopac_results_updated_at
BEFORE UPDATE ON public.mopac_results
FOR EACH ROW EXECUTE PROCEDURE update_updated_at();

-- Configurar as políticas de segurança (RLS - Row Level Security)
-- Ativar RLS nas tabelas
ALTER TABLE public.molecules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.calculations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.crest_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mopac_results ENABLE ROW LEVEL SECURITY;

-- Criar política para permitir acesso de leitura para todos (incluindo usuários anônimos)
CREATE POLICY read_all_molecules ON public.molecules FOR SELECT USING (true);
CREATE POLICY read_all_calculations ON public.calculations FOR SELECT USING (true);
CREATE POLICY read_all_crest_results ON public.crest_results FOR SELECT USING (true);
CREATE POLICY read_all_mopac_results ON public.mopac_results FOR SELECT USING (true);

-- Criar política para permitir inserções de usuários anônimos
CREATE POLICY insert_molecules ON public.molecules FOR INSERT WITH CHECK (true);
CREATE POLICY insert_calculations ON public.calculations FOR INSERT WITH CHECK (true);
CREATE POLICY insert_crest_results ON public.crest_results FOR INSERT WITH CHECK (true);
CREATE POLICY insert_mopac_results ON public.mopac_results FOR INSERT WITH CHECK (true);

-- Criar política para permitir atualizações de usuários anônimos
CREATE POLICY update_molecules ON public.molecules FOR UPDATE USING (true);
CREATE POLICY update_calculations ON public.calculations FOR UPDATE USING (true);
CREATE POLICY update_crest_results ON public.crest_results FOR UPDATE USING (true);
CREATE POLICY update_mopac_results ON public.mopac_results FOR UPDATE USING (true);

-- Conceder permissões ao papel anônimo (necessário para acesso pela API)
GRANT SELECT, INSERT, UPDATE ON public.molecules TO anon;
GRANT SELECT, INSERT, UPDATE ON public.calculations TO anon;
GRANT SELECT, INSERT, UPDATE ON public.crest_results TO anon;
GRANT SELECT, INSERT, UPDATE ON public.mopac_results TO anon;

-- Permitir que usuários anônimos utilizem as sequências de ID
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon;

-- Configuração Storage (nota: esta parte precisa ser feita manualmente no painel de administração)
-- 1. Crie um bucket chamado 'molecule-files'
-- 2. Configure a política de segurança do bucket para permitir operações de leitura/gravação

-- FIM DO SCRIPT

-- Instruções para configurar o Storage no Supabase:
-- 1. Acesse o painel de administração do Supabase
-- 2. Vá para a seção "Storage"
-- 3. Clique em "Create new bucket"
-- 4. Digite o nome "molecule-files"
-- 5. Marque a opção "Public" para permitir acesso anônimo aos arquivos (opcional)
-- 6. Clique em "Create bucket"
-- 7. Depois de criar o bucket, configure as políticas de segurança conforme necessário
