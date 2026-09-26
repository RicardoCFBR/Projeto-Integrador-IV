# Arquitetura — baseline

```text
Dispositivos Android / Simulador
            ↓
      Telemetria JSON
            ↓
        API Backend
            ↓
 ┌──────────┴──────────┐
 ↓                     ↓
Persistência        Inferência ML
 ↓                     ↓
 └──────────┬──────────┘
            ↓
       Dashboard Web
```

## Princípios

- arquitetura em camadas;
- integração incremental;
- ML desacoplado da interface;
- dados reais e sintéticos claramente separados;
- possibilidade de substituir o simulador por coleta real futuramente;
- evitar chamar a arquitetura de microsserviços enquanto não houver serviços independentes implantados.
