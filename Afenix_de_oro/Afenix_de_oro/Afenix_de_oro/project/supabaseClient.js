import { createClient } from '@supabase/supabase-js'

// Aquí pegas la URL de tu proyecto de Supabase y tu clave anónima (anon/public)
const SUPABASE_URL = 'https://juviuwuwopyceshxutqe.supabase.co'
const SUPABASE_ANON_KEY = 'sb_publishable_uthxT5lumUiVzMUfCcJR0w_QVohSNTO'

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)