# 🚀 Deploy Frontend no Railway

Guia completo para fazer deploy do frontend React/Next.js no Railway.

## 📋 Pré-requisitos

- Conta no Railway
- Repositório Git com o código
- API backend já deployada

## 🎯 Opções de Deploy

### **Opção 1: Deploy Separado (Recomendado)**

#### **1.1 Frontend (Next.js)**

```bash
# 1. Crie um novo projeto no Railway
# 2. Conecte seu repositório
# 3. Configure o diretório: frontend/
# 4. Configure as variáveis de ambiente
```

**Variáveis de Ambiente:**

```env
API_URL=https://sua-api.railway.app
WS_URL=wss://sua-api.railway.app
NODE_ENV=production
```

**Build Command:**

```bash
npm run build
```

**Start Command:**

```bash
npm start
```

#### **1.2 API (FastAPI)**

```bash
# 1. Crie outro projeto no Railway
# 2. Conecte o mesmo repositório
# 3. Configure o diretório: ./
# 4. Configure as variáveis de ambiente
```

**Variáveis de Ambiente:**

```env
DATABASE_URL=postgresql://...
CELERY_BROKER_URL=postgresql://...
SECRET_KEY=sua-chave-secreta
```

### **Opção 2: Deploy Unificado**

Use o `railway.json` para configurar múltiplos serviços:

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "npm start",
    "healthcheckPath": "/",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

## 🔧 Configurações Específicas

### **Next.js Configuration**

```javascript
// next.config.js
const nextConfig = {
  output: "standalone", // Para Railway
  env: {
    API_URL: process.env.API_URL,
    WS_URL: process.env.WS_URL,
  },
};
```

### **Docker Configuration**

```dockerfile
# Dockerfile para Railway
FROM node:18-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 🌐 Domínios e SSL

### **Domínio Personalizado**

1. Vá para Settings > Domains
2. Adicione seu domínio
3. Configure DNS:
   ```
   CNAME frontend.seudominio.com -> railway.app
   ```

### **SSL Automático**

- Railway fornece SSL automático
- Certificados Let's Encrypt
- HTTPS habilitado por padrão

## 📊 Monitoramento

### **Health Checks**

```javascript
// pages/api/health.js
export default function handler(req, res) {
  res.status(200).json({ status: "healthy" });
}
```

### **Logs**

- Acesse via Railway Dashboard
- Logs em tempo real
- Histórico de deployments

## 🔄 CI/CD

### **GitHub Actions**

```yaml
name: Deploy to Railway
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: railway/deploy@v1
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
```

## 💰 Custos

### **Plano Gratuito**

- $5 de crédito mensal
- Ideal para desenvolvimento/teste

### **Plano Pago**

- $20/mês
- Recursos ilimitados
- Domínios personalizados

## 🚀 Comandos Úteis

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Deploy
railway up

# Ver logs
railway logs

# Abrir no browser
railway open
```

## 🎯 Estrutura Final

```
seu-projeto/
├── frontend/          # Next.js App
│   ├── pages/
│   ├── components/
│   ├── package.json
│   └── Dockerfile
├── app/              # FastAPI Backend
│   ├── main.py
│   └── ...
├── docker-compose.yml
└── railway.json
```

## ✅ Checklist de Deploy

- [ ] Repositório conectado ao Railway
- [ ] Variáveis de ambiente configuradas
- [ ] Build command configurado
- [ ] Start command configurado
- [ ] Health check funcionando
- [ ] Domínio configurado (opcional)
- [ ] SSL funcionando
- [ ] Frontend conectando com API
- [ ] Testes realizados

## 🆘 Troubleshooting

### **Build Fails**

- Verifique dependências no package.json
- Confirme Node.js version
- Verifique scripts de build

### **Runtime Errors**

- Verifique variáveis de ambiente
- Confirme URLs da API
- Verifique logs do Railway

### **CORS Issues**

- Configure CORS na API
- Verifique domínios permitidos
- Use proxy no Next.js se necessário
