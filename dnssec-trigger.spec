%global _hardened_build 1

Summary: NetworkManager plugin to update/reconfigure DNSSEC resolving
Name: dnssec-trigger
Version: 0.11
Release: 22%{?dist}
License: BSD
Url: http://www.nlnetlabs.nl/downloads/dnssec-trigger/
Source: http://www.nlnetlabs.nl/downloads/dnssec-trigger/%{name}-%{version}.tar.gz
Source1:dnssec-triggerd.service
Source2: dnssec-triggerd-keygen.service
Source3: dnssec-trigger.conf
# Latest NM dispatcher Python hook from upstream SVN
# http://www.nlnetlabs.nl/svn/dnssec-trigger/trunk/contrib/01-dnssec-trigger-hook-new_nm
Source4: 01-dnssec-trigger-hook
Source5: dnssec-trigger.tmpfiles.d
Source6: dnssec-triggerd-resolvconf-handle.sh
Source7: dnssec-triggerd-resolvconf-handle.service
# http://www.nlnetlabs.nl/svn/dnssec-trigger/trunk/contrib/dnssec.conf.sample
Source8: dnssec.conf.sample
Patch1: dnssec-trigger-0.11-improve_dialog_texts.patch
Patch2: dnssec-trigger-842455.patch
# https://www.nlnetlabs.nl/bugs-script/show_bug.cgi?id=489
Patch3: dnssec-trigger-0.11-nl489.patch
Patch4: dnssec-trigger-0.11-coverity_scan.patch
Patch5: dnssec-trigger-rh1254473.patch

Requires(postun): initscripts
Requires: ldns >= 1.6.10, NetworkManager, NetworkManager-glib, unbound, xdg-utils
Requires(pre): shadow-utils
BuildRequires: desktop-file-utils systemd-units, openssl-devel, ldns-devel
BuildRequires: gtk2-devel, NetworkManager-devel

BuildRequires: systemd
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

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
# change some text in the popups
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p1

%build
%configure  --with-keydir=/etc/dnssec-trigger 
%{__make} %{?_smp_mflags}

%install
rm -rf %{buildroot}
%{__make} DESTDIR=%{buildroot} install
install -d 0755 %{buildroot}%{_unitdir}
install -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/%{name}d.service
install -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}/%{name}d-keygen.service
install -m 0644 %{SOURCE3} %{buildroot}%{_sysconfdir}/%{name}/

mkdir -p %{buildroot}%{_libexecdir}
install -m 0755 %{SOURCE6} %{buildroot}%{_libexecdir}/%{name}d-resolvconf-handle.sh
install -m 0644 %{SOURCE7} %{buildroot}%{_unitdir}/%{name}d-resolvconf-handle.service

desktop-file-install --dir=%{buildroot}%{_datadir}/applications dnssec-trigger-panel.desktop

# overwrite the stock NM hook since there is new one in upstream SVN that is not used by default
install -p -m 0755 %{SOURCE4} %{buildroot}/%{_sysconfdir}/NetworkManager/dispatcher.d/01-dnssec-trigger-hook
#install the /etc/dnssec.conf configuration file
install -p -m 0644 %{SOURCE8} %{buildroot}/%{_sysconfdir}/dnssec.conf

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
%{_unitdir}/%{name}d-resolvconf-handle.service

%attr(0755,root,root) %dir %{_sysconfdir}/%{name}
%attr(0755,root,root) %{_sysconfdir}/NetworkManager/dispatcher.d/01-dnssec-trigger-hook
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/dnssec.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/dnssec-trigger.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/xdg/autostart/dnssec-trigger-panel.desktop
%dir %{_localstatedir}/run/%{name}
%{_tmpfilesdir}/%{name}.conf
%{_bindir}/dnssec-trigger-panel
%{_bindir}/dnssec-trigger
%{_sbindir}/dnssec-trigger*
%{_libexecdir}/%{name}d-resolvconf-handle.sh
%{_mandir}/*/*
%attr(0755,root,root) %dir %{_datadir}/%{name}
%attr(0644,root,root) %{_datadir}/%{name}/*
%attr(0644,root,root) %{_datadir}/applications/dnssec-trigger-panel.desktop


%post
%systemd_post %{name}d.service


%preun
%systemd_preun %{name}d.service
if [ "$1" -eq "0" ] ; then
    # dnssec-triggerd makes /etc/resolv.conf immutable, undo that on removal
    chattr -i /etc/resolv.conf
fi

%postun
%systemd_postun_with_restart %{name}d.service


%changelog
* Wed May 18 2016 Tomas Hozza <thozza@redhat.com> - 0.11-22
- Improved text in the GUI panel in Hotspot sign-on mode (#1254473)
- Build all binaries with PIE hardening (#1092526)

* Tue Feb 11 2014 Tomas Hozza <thozza@redhat.com> - 0.11-21
- handle IndexError exception in NM script until NM provides better API (#1063735)
- restart NM when stopping dnssec-trigger daemon instead of handling
  resolv.conf by ourself. (#1061370)

* Wed Jan 29 2014 Tomas Hozza <thozza@redhat.com> - 0.11-20
- use systemd macros instead of directly using systemctl (#1058773)
- Replace the "Fedora /EPEL" comment in dnssec-trigger.conf (#1055949)
- Use more newer and more advanced dispatcher script (#1034813)

* Fri Jan 24 2014 Daniel Mach <dmach@redhat.com> - 0.11-19
- Mass rebuild 2014-01-24

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 0.11-18
- Mass rebuild 2013-12-27

* Tue Nov 26 2013 Tomas Hozza <thozza@redhat.com> - 0.11-17
- Add script to backup and restore resolv.conf on dnssec-trigger start/stop (#1031648)

* Mon Nov 18 2013 Tomas Hozza <thozza@redhat.com> - 0.11-16
- Improve GUI dialogs texts (#1029889)

* Mon Nov 11 2013 Tomas Hozza <thozza@redhat.com> - 0.11-15
- Fix the dispatcher script to use new nmcli syntax (#1028003)

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
