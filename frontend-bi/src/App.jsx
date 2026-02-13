/* Para que eslint no se queje de las variables no usadas */
import React, { useState, useCallback, useRef, useEffect } from 'react';
import { GraphicWalker } from '@kanaries/graphic-walker';
import './App.css';
import logo from './assets/logo.png';

/* Tipos de gráficos que se pueden generar */
const CHART_TYPES = [
  { id: 'bar', label: 'Barras' },
  { id: 'line', label: 'Líneas' },
  { id: 'area', label: 'Área' },
  { id: 'arc', label: 'Pastel' },
  { id: 'point', label: 'Dispersión' },
];

/* Tema personalizado para GraphicWalker */
const CUSTOM_UI_THEME = {
  light: {
    background: '#fffaf4',
    foreground: '#3b2f1e',
    primary: '#d39f5a',
    'primary-foreground': '#000000',
    muted: '#f0e0c8',
    'muted-foreground': '#7a6a52',
    accent: '#f4d4a1',
    'accent-foreground': '#000000',
    border: '#d4b68a',
    ring: '#d39f5a',
    card: '#fff6ec',
    'card-foreground': '#3b2f1e',
    popover: '#fffaf4',
    'popover-foreground': '#3b2f1e',
    secondary: '#f0e0c8',
    'secondary-foreground': '#3b2f1e',
    input: '#fff1e0',
    dimension: '#3b2f1e',
    measure: '#d39f5a',
  },

  /* Tema oscuro */
  dark: { 
    background: '#1e1a15',
    foreground: '#e8dac6',
    primary: '#d39f5a',
    'primary-foreground': '#000000',
    muted: '#2d261f',
    'muted-foreground': '#9a8a72',
    accent: '#352e26',
    'accent-foreground': '#e8dac6',
    border: '#4a3f34',
    ring: '#d39f5a',
    card: '#241f1a',
    'card-foreground': '#e8dac6',
    popover: '#1e1a15',
    'popover-foreground': '#e8dac6',
    secondary: '#2d261f',
    'secondary-foreground': '#e8dac6',
    input: '#2d261f',
    dimension: '#e8dac6',
    measure: '#d39f5a',
  }
};
/* Componente para manejar errores en GraphicWalker */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError(error) { return { hasError: true }; }
  componentDidCatch(error, errorInfo) { 
    console.error("GraphicWalker Error Boundary:", error, errorInfo); 
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="viz-empty" style={{ color: '#ef4444', textAlign: 'center', padding: '20px' }}>
          <h3 style={{ marginBottom: '10px' }}>⚠️ Error de Visualización</h3>
          <p style={{ fontSize: '0.85rem', color: '#7a6a52', maxWidth: '300px', margin: '0 auto 15px' }}>
            Hubo un problema al renderizar el gráfico. Los datos están seguros, intenta reintentar o cambiar el tipo de gráfico.
          </p>
          <button 
            onClick={() => {
              this.setState({ hasError: false });
              if (this.props.onReset) this.props.onReset();
            }} 
            className="suggestion-btn"
            style={{ margin: '0 auto', display: 'block' }}
          >
            Reintentar Visualización
          </button>
        </div>
      );
    }
    return this.props.children; 
  }
}

/* Componente principal */
const App = () => {
  const [messages, setMessages] = useState([]);
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [theme, setTheme] = useState('light');
  const [vizState, setVizState] = useState({
    data: [],
    fields: [],
    chart: null,
    type: 'bar',
    key: 0
  });
  const chatEndRef = useRef(null);
/* Para hacer scroll al final del chat */
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const toggleTheme = () => setTheme(prev => prev === 'light' ? 'dark' : 'light');

/* Genera los campos del gráfico a partir de los datos */
  const generateFields = useCallback((data) => {
    if (!data || !Array.isArray(data) || data.length === 0) return [];
    const sample = data[0];
    return Object.keys(sample).map(key => {
      const value = sample[key];
      let semanticType = 'nominal';
      let analyticType = 'dimension';
      let dataType = 'string';

/* Detecta el tipo de dato */
      if (typeof value === 'number') {
        semanticType = 'quantitative';
        analyticType = 'measure';
        dataType = 'number';
      } else if (typeof value === 'string' && value.includes('-') && !isNaN(Date.parse(value))) {
        semanticType = 'temporal';
        dataType = 'datetime';
      }

/* Crea el campo */
      const f = {
        fid: String(key),
        name: key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' '),
        semanticType,
        analyticType,
        dataType, 
        basename: String(key),
      };

/* Invariant redundante para GraphicWalker 0.4.80 */
      return {
        ...f,
        key: f.fid,
        id: f.fid,
        dragId: f.fid
      };
    });
  }, []);

/* Genera la especificación del gráfico */
  const generateChartSpec = useCallback((fields, type) => {
    if (!fields || !Array.isArray(fields) || fields.length === 0) return null;
    
    const dimensions = fields.filter(f => f.analyticType === 'dimension');
    const measures = fields.filter(f => f.analyticType === 'measure');
    
    if (measures.length === 0) return null;

    const dimField = dimensions.length > 0 ? dimensions[0] : null;
    const measField = measures[0];

    const mapField = (f, extra = {}) => ({
      fid: f.fid,
      name: f.name || f.fid,
      analyticType: f.analyticType || 'dimension',
      semanticType: f.semanticType || 'nominal',
      dataType: f.dataType || 'string',
      basename: f.fid,
      dragId: f.fid,
      ...extra
    });

    // Encodings exhaustivos para evitar el error de length en visSpecHistory.ts
    const encodings = {
      dimensions: dimensions.map(d => mapField(d)),
      measures: measures.map(m => mapField(m)),
      rows: [ mapField(measField, { aggName: 'sum' }) ],
      columns: dimField ? [ mapField(dimField) ] : [],
      color: dimField && type !== 'line' && type !== 'area' ? [ mapField(dimField) ] : [],
      opacity: [], 
      size: [], 
      shape: [], 
      theta: [], 
      radius: [], 
      details: [], 
      filters: [], 
      text: [],
      longitude: [],
      latitude: [],
      geoId: [],
      facetX: [],
      facetY: [],
      facetRows: [],
      facetColumns: []
    };

/* Tipo de gráfico circular */
    if (type === 'arc') {
      encodings.columns = [];
      encodings.rows = [];
      encodings.theta = [ mapField(measField, { aggName: 'sum' }) ];
      if (dimField) {
        encodings.color = [ mapField(dimField) ];
      }
    }
    
    return [{
      visId: 'auto-chart-main',
      name: 'Análisis IA',
      encodings,
      config: { 
        defaultAggregated: true, 
        geoms: [type === 'arc' ? 'arc' : type], 
      },
      layout: { 
        showTableSummary: false, 
        size: { mode: 'full', width: 800, height: 600 } 
      },
    }];
  }, []);

  /* Maneja el cambio de tipo de gráfico */
  const handleChartTypeChange = useCallback((type) => {
    if (vizState.fields.length > 0) {
      const newChart = generateChartSpec(vizState.fields, type);
      setVizState(prev => ({
        ...prev,
        type,
        chart: newChart,
        key: prev.key + 1
      }));
    }
  }, [vizState.fields, generateChartSpec]);

  /* Maneja la pregunta al backend */
  const handleAskBackend = useCallback(async () => {
    if (!prompt.trim() || loading) return;
    const userMsg = prompt.trim();
    setPrompt("");
    setLoading(true);
    setVizState({ data: [], fields: [], chart: null, type: 'bar', key: Date.now() });
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);

    try {

      const resp = await fetch('http://api:8000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: userMsg })
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail || resp.statusText);
      }

 /* Convierte la respuesta a JSON */
      const result = await resp.json();

      if (result.status === 'success') {
        const dataArr = Array.isArray(result.data) ? result.data : [];
        const fieldsData = generateFields(dataArr);
        
        if (dataArr.length > 0 && fieldsData.length > 0) {
          const sType = result.metadata?.suggested_chart || 'bar';
          const spec = generateChartSpec(fieldsData, sType);
          setVizState(prev => ({
            data: dataArr,
            fields: fieldsData,
            chart: spec,
            type: sType,
            key: prev.key + 1
          }));
        }

/* Añade la respuesta del asistente */
        setMessages(prev => [...prev, {
          role: 'assistant',
          text: result.answer || (result.data?.length > 0 ? `Se encontraron ${result.data.length} resultados.` : 'Sin resultados.')
        }]);
      } else {
        // Manejo de errores devueltos por la API (status: 'error')
        setMessages(prev => [...prev, {
          role: 'assistant',
          text: result.answer || 'Lo siento, el servidor devolvió un error desconocido.'
        }]);
      }
    } catch (err) {
      console.error("Fetch Error:", err);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        text: `Lo siento, ha ocurrido un problema: ${err.message}.` 
      }]);
    } finally {
      setLoading(false);
    }
  }, [prompt, loading, generateFields, generateChartSpec]);

  return (
    <div className={`app-container ${theme === 'dark' ? 'dark-theme' : ''}`}>

      {/* Panel izquierdo: Chat */}
      <div className="chat-panel">

        {/* Header */}
        <div className="chat-header">
          <img src={logo} alt="Logo" className={`header-logo${loading ? ' spinning' : ''}`} />
          <div className="chat-header-text">
            <h2>Asistente BI</h2>
            <small>Gemini AI · PostgreSQL</small>
          </div>
          <div className={`theme-switcher-grid ${theme === 'dark' ? 'night-theme' : ''}`} onClick={toggleTheme}>
            <div className="sun"></div>
            <div className="moon-overlay"></div>
            <div className="cloud-ball" id="ball1"></div>
            <div className="cloud-ball" id="ball2"></div>
            <div className="cloud-ball" id="ball3"></div>
            <div className="cloud-ball" id="ball4"></div>
            <div className="star" id="star1"></div>
            <div className="star" id="star2"></div>
            <div className="star" id="star3"></div>
            <div className="star" id="star4"></div>
          </div>
        </div>

        {/* Mensajes */}
        <div className="chat-messages">
          {messages.length === 0 && (
            <div style={{ textAlign: 'left', color: '#7a6a52', marginTop: '20px', marginBottom: '20px' }}>
              <p style={{ fontSize: '0.85rem', fontWeight: 400, lineHeight: 1.6 }}>
                Escribe una pregunta para consultar tu base de datos. <br /> Consultas sugeridas:
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginTop: '40px' }}>
                {[
                  'Rendimiento de los vendedores',
                  'Ventas por categoría',
                  'Ventas por región'
                ].map(q => (
                  <button key={q} onClick={() => setPrompt(q)} className="suggestion-btn">
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
          {/* Muestra los mensajes */}
          {messages.map((msg, i) => (
            <div key={i} style={{
              marginBottom: '12px',
              display: 'flex', flexDirection: 'column',
              alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start'
            }}>
              <div
                className={msg.role === 'user' ? 'msg-bubble-user' : 'msg-bubble-assistant'}
                style={{
                  maxWidth: '90%', padding: '10px 14px', borderRadius: '12px',
                  fontSize: '0.88rem', lineHeight: 1.5
                }}
              >
                {msg.text}
              </div>
              <small style={{ color: '#9a8a72', marginTop: '3px', fontSize: '0.7rem' }}>
                {msg.role === 'user' ? 'Tú' : 'IA'}
              </small>
            </div>
          ))}

        {/* Muestra el loading (cargando) */}
          {loading && (
            <div style={{ color: '#7a6a52', fontSize: '0.85rem', padding: '8px' }}>
              <span style={{ animation: 'pulse 1.5s infinite' }}>⏳</span> Analizando...
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input */}
        <div className="chat-input-area">
          <div className="chat-input-row">
            <textarea
              id="chat-prompt"
              name="chat-prompt"
              value={prompt}
              onChange={(e) => {
                setPrompt(e.target.value);
                e.target.style.height = 'auto';
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
              }}
              placeholder="Escribe tu consulta..."
              className="chat-input"
              rows={1}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleAskBackend();
                }
              }}
            />
            <button
              onClick={handleAskBackend}
              disabled={loading || !prompt.trim()}
              className={`chat-send-btn ${loading || !prompt.trim() ? 'disabled' : 'active'}`}
              style={{ alignSelf: 'center' }}
            >
              {loading ? '⏳' : '➤'}
            </button>
          </div>
        </div>
      </div>

      {/* Panel derecho: Visualización */}
      <div className="viz-panel">
        {vizState.data && vizState.data.length > 0 ? (
          <>
            <div className="chart-type-bar">
              {CHART_TYPES.map(ct => (
                <button
                  key={ct.id}
                  className={`chart-type-btn ${vizState.type === ct.id ? 'active' : ''}`}
                  onClick={() => handleChartTypeChange(ct.id)}
                  title={ct.label}
                >
                  <span className="chart-type-label">{ct.label}</span>
                </button>
              ))}
            </div>
            <div className="viz-content">
                <ErrorBoundary 
                  key={vizState.key}
                  onReset={() => setVizState(prev => ({ ...prev, key: Date.now() }))}
                >
                  <GraphicWalker
                    key={vizState.key}
                    data={vizState.data || []}
                    fields={vizState.fields}
                    chart={Array.isArray(vizState.chart) ? vizState.chart : undefined} 
                    dark={theme === 'dark' ? 'dark' : 'light'}
                    colorConfig={CUSTOM_UI_THEME}
                    i18nLang="es-ES"
                  />
                </ErrorBoundary>
            </div>
          </>
        ) : (
          <div className="viz-empty">
            <div className="viz-empty-icon">
              <img src={logo} alt="Logo" />
            </div>
            <h3>Centro de Visualización</h3>
            <p>
              Realiza una consulta para generar visualizaciones interactivas de tus datos.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
