Summary: NetworkManager plugin to update/reconfigure DNSSEC resolving
Name: dnssec-trigger
Version: 0.11
Release: 14%{?dist}
License: BSD
Url: http://www.nlnetlabs.nl/downloads/dnssec-trigger/
Source: http://www.nlnetlabs.nl/downloads/dnssec-trigger/%{name}-%{version}.tar.gz
Source1:dnssec-triggerd.service
Source2: dnssec-triggerd-keygen.service
Source3: dnssec-trigger.conf
# Latest NM dispatcher hook from upstream SVN
# http://www.nlnetlabs.nl/svn/dnssec-trigger/trunk/01-dnssec-trigger-hook.sh.in
Source4: 01-dnssec-trigger-hook
Source5: dnssec-trigger.tmpfiles.d
Patch1: dnssec-trigger-0.11-gui.patch
Patch2: dnssec-trigger-842455.patch
# https://www.nlnetlabs.nl/bugs-script/show_bug.cgi?id=489
Patch3: dnssec-trigger-0.11-nl489.patch
Patch4: dnssec-trigger-0.11-coverity_scan.patch

Requires(postun): initscripts
Requires: ldns >= 1.6.10, NetworkManager, unbound, xdg-utils
Requires(pre): shadow-utils
BuildRequires: desktop-file-utils systemd-units, openssl-devel, ldns-devel
BuildRequires: gtk2-devel, NetworkManager-devel

Requires(post): systemd-sysv
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units

%description
dnssec-trigger reconfigures the local unbound DNS server. This unbound DNS
server performs DNSSEC validation, but dnssec-trigger will signal it to
use the DHCP obtained forwarders if possible, and fallback to doing its
own AUTH queries if that fails, and if that fails prompt the user via
dnssec-trigger-applet the option to go with insecure DNS only.

%prep
%setup -q 
# Fixup the name to not include "panel" in the menu item or name
sed -i "s/ Panel//" panel/dnssec-trigger-panel.desktop.in
sed -i "s/-panel//" panel/dnssec-trigger-panel.desktop.in
# NM has no /usr/sbin in path
sed -i "s/^dnssec-trigger-control/\/usr\/sbin\/dnssec-trigger-control/" 01-dnssec-trigger-hook.sh.in
# change some text in the popups
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1

%build
export LDFLAGS="$LDFLAGS -Wl,-z,now"

%configure  --with-keydir=/etc/dnssec-trigger 
%{__make} %{?_smp_mflags}

%install
rm -rf %{buildroot}
%{__make} DESTDIR=%{buildroot} install
install -d 0755 %{buildroot}%{_unitdir}
install -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/%{name}d.service
install -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}/%{name}d-keygen.service
install -m 0644 %{SOURCE3} %{buildroot}%{_sysconfdir}/%{name}/

desktop-file-install --dir=%{buildroot}%{_datadir}/applications dnssec-trigger-panel.desktop

# overwrite the stock NM hook since there is new one in upstream SVN that has not been released yet
cp -p %{SOURCE4} %{buildroot}/%{_sysconfdir}/NetworkManager/dispatcher.d/01-dnssec-trigger-hook

# install the configuration for /var/run/dnssec-trigger into tmpfiles.d dir
mkdir -p %{buildroot}%{_tmpfilesdir}
install -m 644 %{SOURCE5} ${RPM_BUILD_ROOT}%{_tmpfilesdir}/%{name}.conf
# we must create the /var/run/dnssec-trigger directory
mkdir -p %{buildroot}%{_localstatedir}/run
install -d -m 0755 %{buildroot}%{_localstatedir}/run/%{name}

# supress the panel name everywhere including the gnome3 panel at the bottom
ln -s dnssec-trigger-panel %{buildroot}%{_bindir}/dnssec-trigger

# Make dnssec-trigger.8 manpage available under names of all dnssec-trigger-*
# executables
for all in dnssec-trigger-control dnssec-trigger-control-setup dnssec-triggerd; do
    ln -s %{_mandir}/man8/dnssec-trigger.8 %{buildroot}/%{_mandir}/man8/"$all".8
done
ln -s %{_mandir}/man8/dnssec-trigger.8 %{buildroot}/%{_mandir}/man8/dnssec-trigger.conf.8

%clean
rm -rf ${RPM_BUILD_ROOT}

%files 
%defattr(-,root,root,-)
%doc README LICENSE
%{_unitdir}/%{name}d.service
%{_unitdir}/%{name}d-keygen.service

%attr(0755,root,root) %dir %{_sysconfdir}/%{name}
%attr(0755,root,root) %{_sysconfdir}/NetworkManager/dispatcher.d/01-dnssec-trigger-hook
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/dnssec-trigger.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/xdg/autostart/dnssec-trigger-panel.desktop
%dir %{_localstatedir}/run/%{name}
%{_tmpfilesdir}/%{name}.conf
%{_bindir}/dnssec-trigger-panel
%{_bindir}/dnssec-trigger
%{_sbindir}/dnssec-trigger*
%{_mandir}/*/*
%attr(0755,root,root) %dir %{_datadir}/%{name}
%attr(0644,root,root) %{_datadir}/%{name}/*
%attr(0644,root,root) %{_datadir}/applications/dnssec-trigger-panel.desktop


%post
# Enable (but don't start) the units by default
    /bin/systemctl enable %{name}d.service >/dev/null 2>&1 || :
    /bin/systemctl enable %{name}d-keygen.service >/dev/null 2>&1 || :


%preun
if [ "$1" -eq "0" ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable %{name}d.service > /dev/null 2>&1 || :
    /bin/systemctl --no-reload disable %{name}d-keygen.service > /dev/null 2>&1 || :
    /bin/systemctl stop %{name}d.service >/dev/null 2>&1 || :
    /bin/systemctl stop %{name}d-keygen.service >/dev/null 2>&1 || :
    # dnssec-triggerd makes /etc/resolv.conf immutable, undo that on removal
    chattr -i /etc/resolv.conf
fi

%postun 
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :

%changelog
* Mon Aug 26 2013 Tomas Hozza <thozza@redhat.com> - 0.11-14
- Fix errors found by static analysis of source

* Fri Aug 09 2013 Tomas Hozza <thozza@redhat.com> - 0.11-13
- Use improved NM dispatcher script from upstream (#980036)
- Added tmpfiles.d config due to improved NM dispatcher script

* Mon Jul 22 2013 Tomas Hozza <thozza@redhat.com> - 0.11-12
- Removed Fedora infrastructure from dnssec-trigger.conf (#955149)

* Mon Mar 04 2013 Adam Tkac <atkac redhat com> - 0.11-11
- link dnssec-trigger.conf.8 to dnssec-trigger.8
- build dnssec-triggerd with full RELRO

* Mon Mar 04 2013 Adam Tkac <atkac redhat com> - 0.11-10
- remove deprecated "Application" keyword from desktop file

* Mon Mar 04 2013 Adam Tkac <atkac redhat com> - 0.11-9
- install various dnssec-trigger-* symlinks to dnssec-trigger.8 manpage

* Wed Feb 13 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.11-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Tue Jan 08 2013 Paul Wouters <pwouters@redhat.com> - 0.11-7
- Use full path for systemd (rhbz#842455)

* Tue Jul 24 2012 Paul Wouters <pwouters@redhat.com> - 0.11-6
- Patched daemon to remove immutable attr (rhbz#842455) as the
  systemd ExecStopPost= target does not seem to work

* Tue Jul 24 2012 Paul Wouters <pwouters@redhat.com> - 0.11-5
- On service stop, remove immutable attr from resolv.conf (rhbz#842455)

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.11-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Thu Jun 28 2012 Paul Wouters <pwouters@redhat.com> - 0.11-3
- Fix DHCP hook for f17+ version of nmcli (rhbz#835298)

* Sun Jun 17 2012 Paul Wouters <pwouters@redhat.com> - 0.11-2
- Small textual changes to some popup windows

* Fri Jun 15 2012 Paul Wouters <pwouters@redhat.com> - 0.11-1
- Updated to 0.11
- http Hotspot detection via fedoraproject.org/static/hotspot.html
- http Hotspot Login page via uses hotspot-nocache.fedoraproject.org

* Thu Feb 23 2012 Paul Wouters <pwouters@redhat.com> - 0.10-4
- Require: unbound

* Wed Feb 22 2012 Paul Wouters <pwouters@redhat.com> - 0.10-3
- Fix the systemd startup to require unbound
- dnssec-triggerd no longer forks, giving systemd more control
- Fire NM dispatcher in ExecStartPost of dnssec-triggerd.service
- Fix tcp80 entries in dnssec-triggerd.conf
- symlink dnssec-trigger-panel to dnssec-trigger to supress the
  "-panel" in the applet name shown in gnome3


* Wed Feb 22 2012 Paul Wouters <pwouters@redhat.com> - 0.10-2
- The NM hook was not modified at the right time during build

* Wed Feb 22 2012 Paul Wouters <pwouters@redhat.com> - 0.10-1
- Updated to 0.10
- The NM hook lacks /usr/sbin in path, resulting in empty resolv.conf on hotspot

* Wed Feb 08 2012 Paul Wouters <pwouters@redhat.com> - 0.9-4
- Updated tls443 / tls80 resolver instances supplied by Fedora Hosted

* Mon Feb 06 2012 Paul Wouters <pwouters@redhat.com> - 0.9-3
- Convert from SysV to systemd for initial Fedora release
- Moved configs and pem files to /etc/dnssec-trigger/
- No more /var/run/dnssec-triggerd/
- Fix Build-requires
- Added commented tls443 port80 entries of pwouters resolvers
- On uninstall ensure there is no immutable bit on /etc/resolv.conf

* Sat Jan 07 2012 Paul Wouters <paul@xelerance.com> - 0.9-2
- Added LICENCE to doc section

* Mon Dec 19 2011 Paul Wouters <paul@xelerance.com> - 0.9-1
- Upgraded to 0.9

* Fri Oct 28 2011 Paul Wouters <paul@xelerance.com> - 0.7-1
- Upgraded to 0.7

* Fri Sep 23 2011 Paul Wouters <paul@xelerance.com> - 0.4-1
- Upgraded to 0.4

* Sat Sep 17 2011 Paul Wouters <paul@xelerance.com> - 0.3-5
- Start 01-dnssec-trigger-hook in daemon start
- Ensure dnssec-triggerd starts after NetworkManager

* Fri Sep 16 2011 Paul Wouters <paul@xelerance.com> - 0.3-4
- Initial package
