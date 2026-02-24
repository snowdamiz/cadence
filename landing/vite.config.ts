import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'node:fs'
import path from 'node:path'

const rootPackageJsonPath = path.resolve(__dirname, '../package.json')
const rootPackageJson = JSON.parse(fs.readFileSync(rootPackageJsonPath, 'utf8')) as {
  version?: unknown
}
const cadenceVersion =
  typeof rootPackageJson.version === 'string' ? rootPackageJson.version : '0.0.0'

export default defineConfig({
  plugins: [react()],
  define: {
    __CADENCE_VERSION__: JSON.stringify(cadenceVersion),
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
