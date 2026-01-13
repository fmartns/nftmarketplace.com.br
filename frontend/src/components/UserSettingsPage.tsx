import { useEffect, useState } from 'react';
import { ImageWithFallback } from './figma/ImageWithFallback';
import { fetchUserProfile, updateUserProfile, verifyHabboNick, getHabboValidationStatus, unlinkHabboNick, confirmHabboValidation, type User } from '@/api/accounts';
import { Skeleton } from './ui/skeleton';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { CheckCircle2, XCircle, Loader2, AlertCircle } from 'lucide-react';

export function UserSettingsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Habbo validation states
  const [habboNick, setHabboNick] = useState('');
  const [habboValidating, setHabboValidating] = useState(false);
  const [habboVerificationStatus, setHabboVerificationStatus] = useState<any>(null);
  const [habboCheckingStatus, setHabboCheckingStatus] = useState(false);
  const [habboError, setHabboError] = useState<string | null>(null);
  const [habboSuccess, setHabboSuccess] = useState<string | null>(null);

  // Form fields
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    cpf: '',
    telefone: '',
    data_nascimento: '',
  });

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);

    (async () => {
      try {
        await new Promise(resolve => setTimeout(resolve, 200));
        
        const token = localStorage.getItem('access_token') || localStorage.getItem('token');
        if (!token) {
          if (!mounted) return;
          setError('Usuário não autenticado');
          setLoading(false);
          return;
        }

        const data = await fetchUserProfile();
        if (!mounted) return;
        setUser(data);
        setFormData({
          username: data.username || '',
          email: data.email || '',
          first_name: data.first_name || '',
          last_name: data.last_name || '',
          cpf: data.cpf || '',
          telefone: data.telefone || '',
          data_nascimento: data.data_nascimento ? data.data_nascimento.split('T')[0] : '',
        });
        setHabboNick(data.nick_habbo || '');
        
        // Check validation status if user has a nick but not validated
        if (data.nick_habbo && !data.habbo_validado) {
          try {
            const status = await getHabboValidationStatus();
            if (mounted) {
              setHabboVerificationStatus(status);
            }
          } catch (e) {
            // Ignore errors when checking status (might not have a validation task)
          }
        } else if (data.nick_habbo && data.habbo_validado) {
          // Clear any previous validation status if already validated
          if (mounted) {
            setHabboVerificationStatus(null);
          }
        }
        
        setError(null);
      } catch (e: any) {
        if (!mounted) return;
        console.error('Erro ao buscar perfil:', e);
        if (e?.message?.includes('401') || e?.message?.includes('403')) {
          setError('Usuário não autenticado. Por favor, faça login novamente.');
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('token');
        } else {
          setError(e?.message || 'Falha ao carregar perfil');
        }
      } finally {
        if (mounted) setLoading(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    setSuccess(false);
  };

  const formatCPF = (value: string) => {
    const numbers = value.replace(/\D/g, '');
    if (numbers.length <= 11) {
      return numbers
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
    }
    return value;
  };

  const formatTelefone = (value: string) => {
    const numbers = value.replace(/\D/g, '');
    if (numbers.length <= 11) {
      if (numbers.length <= 10) {
        return numbers
          .replace(/(\d{2})(\d)/, '($1) $2')
          .replace(/(\d{4})(\d)/, '$1-$2');
      } else {
        return numbers
          .replace(/(\d{2})(\d)/, '($1) $2')
          .replace(/(\d{5})(\d)/, '$1-$2');
      }
    }
    return value;
  };

  const handleCPFChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatCPF(e.target.value);
    setFormData(prev => ({ ...prev, cpf: formatted }));
    setSuccess(false);
  };

  const handleTelefoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatTelefone(e.target.value);
    setFormData(prev => ({ ...prev, telefone: formatted }));
    setSuccess(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(false);

    // Map field names to friendly names
    const fieldNames: Record<string, string> = {
      email: 'E-mail',
      first_name: 'Nome',
      last_name: 'Sobrenome',
      cpf: 'CPF',
      telefone: 'Telefone',
      data_nascimento: 'Data de Nascimento',
    };

    // Validate required fields
    if (!formData.email || formData.email.trim() === '') {
      setError('E-mail é obrigatório.');
      setSaving(false);
      return;
    }

    try {
      // Convert empty strings to null for optional fields
      const dataToSend = {
        email: formData.email,
        first_name: formData.first_name || null,
        last_name: formData.last_name || null,
        cpf: formData.cpf || null,
        telefone: formData.telefone || null,
        data_nascimento: formData.data_nascimento || null,
      };
      
      const updatedUser = await updateUserProfile(dataToSend);
      setUser(updatedUser);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (e: any) {
      console.error('Erro ao atualizar perfil:', e);
      
      // Try to parse validation errors
      let errorMessage = 'Falha ao atualizar perfil';
      
      if (e?.response) {
        // Handle structured validation errors
        const errors: string[] = [];
        for (const [key, value] of Object.entries(e.response)) {
          const fieldName = fieldNames[key] || key;
          if (Array.isArray(value)) {
            value.forEach((msg: string) => {
              if (msg.includes('obrigatório') || msg.includes('required')) {
                errors.push(`${fieldName} é obrigatório.`);
              } else {
                errors.push(`${fieldName}: ${msg}`);
              }
            });
          } else if (typeof value === 'string') {
            if (value.includes('obrigatório') || value.includes('required')) {
              errors.push(`${fieldName} é obrigatório.`);
            } else {
              errors.push(`${fieldName}: ${value}`);
            }
          }
        }
        if (errors.length > 0) {
          errorMessage = errors.join(' ');
        }
      } else if (e?.message) {
        // Handle simple error messages
        let msg = e.message;
        // Remove technical prefixes
        if (msg.includes('failed:')) {
          const parts = msg.split('failed:');
          if (parts.length > 1) {
            msg = parts[parts.length - 1].trim();
            // Try to parse as JSON if it looks like JSON
            try {
              const parsed = JSON.parse(msg);
              if (typeof parsed === 'object' && parsed !== null) {
                // Treat as structured error
                const errors: string[] = [];
                for (const [key, value] of Object.entries(parsed)) {
                  const fieldName = fieldNames[key] || key;
                  if (Array.isArray(value)) {
                    value.forEach((v: string) => {
                      if (v.includes('obrigatório') || v.includes('required') || v === 'Este campo é obrigatório.') {
                        errors.push(`${fieldName} é obrigatório.`);
                      } else {
                        errors.push(`${fieldName}: ${v}`);
                      }
                    });
                  } else if (typeof value === 'string') {
                    if (value.includes('obrigatório') || value.includes('required') || value === 'Este campo é obrigatório.') {
                      errors.push(`${fieldName} é obrigatório.`);
                    } else {
                      errors.push(`${fieldName}: ${value}`);
                    }
                  }
                }
                if (errors.length > 0) {
                  errorMessage = errors.join(' ');
                }
              }
            } catch {
              // Not JSON, continue with string processing
            }
          }
        }
        
        // Map generic messages if not already processed
        if (errorMessage === 'Falha ao atualizar perfil' && msg) {
          if (msg.includes('obrigatório') || msg.includes('required') || msg === 'Este campo é obrigatório.') {
            // Try to extract field name from context
            let found = false;
            for (const [key, friendlyName] of Object.entries(fieldNames)) {
              if (msg.toLowerCase().includes(key)) {
                errorMessage = `${friendlyName} é obrigatório.`;
                found = true;
                break;
              }
            }
            if (!found) {
              errorMessage = 'Por favor, preencha todos os campos obrigatórios.';
            }
          } else {
            errorMessage = msg;
          }
        }
      }
      
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleVerifyHabbo = async () => {
    if (!habboNick.trim()) {
      setHabboError('Por favor, insira um nick do Habbo');
      return;
    }

    setHabboValidating(true);
    setHabboError(null);
    setHabboSuccess(null);

    try {
      const response = await verifyHabboNick({ nick_habbo: habboNick.trim() });
      setHabboVerificationStatus({
        id: response.validation_id,
        nick_habbo: response.nick_habbo,
        palavra_validacao: response.palavra_validacao,
        status: 'pending',
      });
      setHabboSuccess(response.message);
      
      // Refresh user profile
      const updatedUser = await fetchUserProfile();
      setUser(updatedUser);
      setHabboNick(updatedUser.nick_habbo || '');
      
      // Start polling for status
      setTimeout(() => {
        startStatusPolling(response.validation_id);
      }, 1000);
    } catch (e: any) {
      console.error('Erro ao iniciar validação:', e);
      // Extract clean error message (remove "POST /path failed: status" prefix if present)
      let errorMsg = e?.message || 'Falha ao iniciar validação do Habbo';
      if (errorMsg.includes('failed:')) {
        const parts = errorMsg.split('failed:');
        if (parts.length > 1) {
          errorMsg = parts[parts.length - 1].trim();
        }
      }
      setHabboError(errorMsg);
    } finally {
      setHabboValidating(false);
    }
  };

  const startStatusPolling = (validationId: number) => {
    // Clear any existing interval
    const existingInterval = (window as any).habboStatusPolling;
    if (existingInterval) {
      clearInterval(existingInterval);
    }

    const interval = setInterval(async () => {
      try {
        const status = await getHabboValidationStatus(validationId);
        setHabboVerificationStatus(status);
        
        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(interval);
          (window as any).habboStatusPolling = null;
          // Refresh user profile
          const updatedUser = await fetchUserProfile();
          setUser(updatedUser);
        }
      } catch (e) {
        console.error('Erro ao verificar status:', e);
        clearInterval(interval);
        (window as any).habboStatusPolling = null;
      }
    }, 10000); // Check every 10 seconds

    (window as any).habboStatusPolling = interval;

    // Clear interval after 5 minutes
    setTimeout(() => {
      clearInterval(interval);
      (window as any).habboStatusPolling = null;
    }, 300000);
  };

  const handleCheckStatus = async () => {
    setHabboCheckingStatus(true);
    setHabboError(null);
    
    try {
      const status = await getHabboValidationStatus();
      setHabboVerificationStatus(status);
      
      if (status.status === 'pending') {
        setTimeout(() => {
          startStatusPolling(status.id);
        }, 1000);
      }
      
      // Refresh user profile
      const updatedUser = await fetchUserProfile();
      setUser(updatedUser);
    } catch (e: any) {
      console.error('Erro ao verificar status:', e);
      let errorMsg = e?.message || 'Falha ao verificar status da validação';
      if (errorMsg.includes('failed:')) {
        const parts = errorMsg.split('failed:');
        if (parts.length > 1) {
          errorMsg = parts[parts.length - 1].trim();
        }
      }
      setHabboError(errorMsg);
    } finally {
      setHabboCheckingStatus(false);
    }
  };

  const handleConfirmManually = async () => {
    setHabboValidating(true);
    setHabboError(null);
    
    try {
      await confirmHabboValidation();
      setHabboSuccess('Validação confirmada! Aguarde alguns instantes.');
      
      // Refresh status and user profile
      setTimeout(async () => {
        await handleCheckStatus();
      }, 2000);
    } catch (e: any) {
      console.error('Erro ao confirmar validação:', e);
      let errorMsg = e?.message || 'Falha ao confirmar validação';
      if (errorMsg.includes('failed:')) {
        const parts = errorMsg.split('failed:');
        if (parts.length > 1) {
          errorMsg = parts[parts.length - 1].trim();
        }
      }
      setHabboError(errorMsg);
    } finally {
      setHabboValidating(false);
    }
  };

  const handleUnlinkHabbo = async () => {
    if (!confirm('Tem certeza que deseja desvincular seu nick do Habbo?')) {
      return;
    }

    setHabboValidating(true);
    setHabboError(null);
    setHabboSuccess(null);

    try {
      await unlinkHabboNick();
      setHabboNick('');
      setHabboVerificationStatus(null);
      setHabboSuccess('Nick desvinculado com sucesso!');
      
      // Refresh user profile
      const updatedUser = await fetchUserProfile();
      setUser(updatedUser);
    } catch (e: any) {
      console.error('Erro ao desvincular:', e);
      let errorMsg = e?.message || 'Falha ao desvincular nick do Habbo';
      if (errorMsg.includes('failed:')) {
        const parts = errorMsg.split('failed:');
        if (parts.length > 1) {
          errorMsg = parts[parts.length - 1].trim();
        }
      }
      setHabboError(errorMsg);
    } finally {
      setHabboValidating(false);
    }
  };


  if (loading) {
    return (
      <div className="relative w-full">
        <div className="relative h-64 lg:h-80 overflow-hidden">
          <ImageWithFallback
            src="https://collectibles.habbo.com/hero-bg-xl.png"
            alt="Profile cover"
            className="w-full h-full object-cover opacity-50"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent" />
          <div className="absolute inset-0 bg-muted/30" />
        </div>
        <div className="container mx-auto px-4 lg:px-8">
          <div className="relative mt-8 lg:mt-12">
            <div className="max-w-2xl mx-auto space-y-6">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error && !user) {
    return (
      <div className="container mx-auto px-4 lg:px-8 py-16">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">Erro ao carregar perfil</h2>
          <p className="text-muted-foreground">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full">
      {/* Cover Image */}
      <div className="relative h-64 lg:h-80 overflow-hidden">
        <ImageWithFallback
          src="https://collectibles.habbo.com/hero-bg-xl.png"
          alt="Profile cover"
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent" />
      </div>

      {/* Profile Info */}
      <div className="container mx-auto px-4 lg:px-8 pb-16 lg:pb-24">
        <div className="relative mt-12 lg:mt-16">
          {/* Settings Form */}
          <div className="max-w-2xl mx-auto">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Messages */}
              {error && (
                <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-md">
                  {error}
                </div>
              )}
              {success && (
                <div className="bg-green-500/10 border border-green-500/20 text-green-500 px-4 py-3 rounded-md">
                  Perfil atualizado com sucesso!
                </div>
              )}

              {/* First Name */}
              <div className="space-y-2">
                <Label htmlFor="first_name">Nome</Label>
                <Input
                  id="first_name"
                  name="first_name"
                  type="text"
                  placeholder="Digite seu nome"
                  value={formData.first_name}
                  onChange={handleInputChange}
                />
              </div>

              {/* Last Name */}
              <div className="space-y-2">
                <Label htmlFor="last_name">Sobrenome</Label>
                <Input
                  id="last_name"
                  name="last_name"
                  type="text"
                  placeholder="Digite seu sobrenome"
                  value={formData.last_name}
                  onChange={handleInputChange}
                />
              </div>

              {/* CPF */}
              <div className="space-y-2">
                <Label htmlFor="cpf">CPF</Label>
                <Input
                  id="cpf"
                  name="cpf"
                  type="text"
                  placeholder="000.000.000-00"
                  value={formData.cpf}
                  onChange={handleCPFChange}
                  maxLength={14}
                />
              </div>

              {/* Email */}
              <div className="space-y-2">
                <Label htmlFor="email">E-mail</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="seu@email.com"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                />
              </div>

              {/* Telefone */}
              <div className="space-y-2">
                <Label htmlFor="telefone">Telefone</Label>
                <Input
                  id="telefone"
                  name="telefone"
                  type="text"
                  placeholder="(00) 00000-0000"
                  value={formData.telefone}
                  onChange={handleTelefoneChange}
                  maxLength={15}
                />
              </div>

              {/* Data de Nascimento */}
              <div className="space-y-2">
                <Label htmlFor="data_nascimento">Data de Nascimento</Label>
                <Input
                  id="data_nascimento"
                  name="data_nascimento"
                  type="date"
                  value={formData.data_nascimento}
                  onChange={handleInputChange}
                />
              </div>

              {/* Submit Button */}
              <div className="pt-4">
                <Button
                  type="submit"
                  className="w-full bg-[#FFE000] hover:bg-[#FFD700] text-black border-0"
                  disabled={saving}
                >
                  {saving ? 'Salvando...' : 'Salvar Alterações'}
                </Button>
              </div>
            </form>

            {/* Habbo Linking Section */}
            <div className="mt-12 pt-8 pb-24 lg:pb-32 border-t border-border/40">
              <h2 className="text-2xl font-bold mb-6">Vincular Conta do Habbo</h2>
              
              {/* Habbo Messages */}
              {habboError && (
                <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-md mb-4 flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-medium mb-1">Erro ao vincular conta</p>
                    <p className="text-sm">{habboError}</p>
                  </div>
                </div>
              )}
              {habboSuccess && (
                <div className="bg-green-500/10 border border-green-500/20 text-green-500 px-4 py-3 rounded-md mb-4">
                  {habboSuccess}
                </div>
              )}

              {user?.nick_habbo && user.habbo_validado ? (
                /* Habbo Linked and Validated */
                <div className="space-y-4">
                  <div className="flex items-center gap-3 p-4 bg-green-500/10 border border-green-500/20 rounded-md">
                    <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0" />
                    <div className="flex-1">
                      <p className="font-medium">Nick Habbo vinculado e validado</p>
                      <p className="text-sm text-muted-foreground">@{user.nick_habbo}</p>
                    </div>
                  </div>
                  
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleUnlinkHabbo}
                    disabled={habboValidating}
                    className="w-full mb-16 lg:mb-24"
                  >
                    {habboValidating ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Desvinculando...
                      </>
                    ) : (
                      'Desvincular Nick'
                    )}
                  </Button>
                </div>
              ) : user?.nick_habbo ? (
                /* Habbo Linked but Not Validated */
                <div className="space-y-4">
                  <div className="flex items-center gap-3 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-md">
                    <AlertCircle className="w-5 h-5 text-yellow-500" />
                    <div className="flex-1">
                      <p className="font-medium">Nick Habbo vinculado - Aguardando validação</p>
                      <p className="text-sm text-muted-foreground">@{user.nick_habbo}</p>
                    </div>
                  </div>

                  {habboVerificationStatus && (
                    <div className="p-4 bg-card border border-border rounded-md space-y-3">
                      <div>
                        <p className="text-sm font-medium mb-2">Instruções:</p>
                        <ol className="text-sm text-muted-foreground space-y-1 list-decimal list-inside">
                          <li>Coloque a palavra abaixo no seu motto do Habbo</li>
                          <li>Aguarde 5 minutos para validação automática</li>
                          <li>Ou clique em "Confirmar Manualmente" após colocar a palavra</li>
                        </ol>
                      </div>
                      
                      <div className="p-3 bg-background rounded border border-border">
                        <p className="text-xs text-muted-foreground mb-1">Palavra de validação:</p>
                        <p className="text-lg font-mono font-bold text-[#FFE000]">
                          {habboVerificationStatus.palavra_validacao}
                        </p>
                      </div>

                      <div className="flex gap-2">
                        <Button
                          type="button"
                          variant="outline"
                          onClick={handleCheckStatus}
                          disabled={habboCheckingStatus}
                          className="flex-1"
                        >
                          {habboCheckingStatus ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              Verificando...
                            </>
                          ) : (
                            'Verificar Status'
                          )}
                        </Button>
                        <Button
                          type="button"
                          onClick={handleConfirmManually}
                          disabled={habboValidating}
                          className="flex-1 bg-[#FFE000] hover:bg-[#FFD700] text-black border-0"
                        >
                          {habboValidating ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              Confirmando...
                            </>
                          ) : (
                            'Confirmar Manualmente'
                          )}
                        </Button>
                      </div>
                    </div>
                  )}

                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleUnlinkHabbo}
                    disabled={habboValidating}
                    className="w-full mb-16 lg:mb-24"
                  >
                    {habboValidating ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Desvinculando...
                      </>
                    ) : (
                      'Desvincular e Vincular Outro'
                    )}
                  </Button>
                </div>
              ) : (
                /* No Habbo Linked */
                <div className="space-y-4">
                  <div className="p-4 bg-muted/50 border border-border rounded-md">
                    <p className="text-sm text-muted-foreground mb-4">
                      Vincule sua conta do Habbo para ter acesso a recursos exclusivos.
                    </p>
                    
                    <div className="space-y-2">
                      <Label htmlFor="habbo_nick">Nick do Habbo</Label>
                      <Input
                        id="habbo_nick"
                        type="text"
                        placeholder="Digite seu nick do Habbo"
                        value={habboNick}
                        onChange={(e) => {
                          setHabboNick(e.target.value);
                          setHabboError(null);
                        }}
                        disabled={habboValidating}
                      />
                    </div>

                    <Button
                      type="button"
                      onClick={handleVerifyHabbo}
                      disabled={habboValidating || !habboNick.trim()}
                      className="w-full mt-4 mb-16 lg:mb-24 bg-[#FFE000] hover:bg-[#FFD700] text-black border-0"
                    >
                      {habboValidating ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Iniciando validação...
                        </>
                      ) : (
                        'Vincular Conta do Habbo'
                      )}
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

