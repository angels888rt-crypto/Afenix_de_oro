import { supabase } from './supabaseClient.js'

async function probarConexion() {
  const { data, error } = await supabase
    .from('_categoria')
    .select('*')

  if (error) {
    console.error('Error al conectar con Supabase:', error)
  } else {
    console.log('¡Conexión exitosa! Estas son las categorías de tu restaurante:', data)
  }
}

probarConexion()